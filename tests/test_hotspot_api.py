"""
AERIS Hotspot API Tests (tests/test_hotspot_api.py)
===================================================
Validates:
1. Response shape conforms strictly to GeoJSON FeatureCollection:
   - type == "FeatureCollection"
   - features list
   - metadata with city="Pune", generatedAt, dataSource="model_estimate"
2. Exactly 3 documented ML junction zones:
   - PUNE_ALANKAR_CHOWK, PUNE_JEHANGIR_CHOWK, PUNE_RTO_CHOWK
   - WGS84 coordinates match documented zone repositories [longitude, latitude]
3. Data provenance strictly 'model_estimate' across all features and metadata (never 'observed' or 'DEMO_FIXTURE').
4. Uniform modeled PM2.5 across all 3 zones:
   - Reflects city-wide CAMS Global atmospheric forecast (not independent per-zone observations).
   - Uniform AQI and CpcbBand derived via canonical CPCB formula.
5. Intensity is clamped to [0, 1] and reflects normalized traffic count:
   - Normalized min-max scaling across zones.
   - Safe fallback of 0.5 when traffic counts are equal or zero.
6. Dominant driver is 'Traffic' (contextual model feature, not causal source apportionment).
7. Missing processed feature dataset returns HTTP 503 Service Unavailable with clear detail message.
8. No valid modeled PM2.5 in dataset returns HTTP 503 Service Unavailable.
9. No demo fallback in real endpoint under any circumstances.
"""

from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.hotspots import get_hotspot_service
from backend.app.schemas.current import CpcbBand
from backend.app.services.hotspot_service import HotspotService
from backend.app.utils.cpcb_aqi import estimate_aqi_from_pm25, get_band_from_aqi


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. Response Shape & Contract Validation
# -----------------------------------------------------------------------------
def test_hotspots_response_shape(client):
    """GET /api/v1/hotspots returns valid GeoJSON FeatureCollection with metadata."""
    resp = client.get("/api/v1/hotspots")
    assert resp.status_code == 200
    data = resp.json()

    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert isinstance(data["features"], list)
    assert len(data["features"]) == 3

    assert "metadata" in data
    meta = data["metadata"]
    assert meta["city"] == "Pune"
    assert "generatedAt" in meta
    assert isinstance(meta["generatedAt"], str)
    assert len(meta["generatedAt"]) > 0


# -----------------------------------------------------------------------------
# 2. Exactly 3 Documented Zones & Coordinates
# -----------------------------------------------------------------------------
def test_hotspots_exactly_three_documented_zones(client):
    """Features contain exactly the 3 documented ML Chowk zones with WGS84 coordinates."""
    resp = client.get("/api/v1/hotspots")
    assert resp.status_code == 200
    data = resp.json()

    features = data["features"]
    assert len(features) == 3

    zone_props = {f["properties"]["id"]: f["properties"] for f in features}
    expected_ids = {"PUNE_ALANKAR_CHOWK", "PUNE_JEHANGIR_CHOWK", "PUNE_RTO_CHOWK"}
    assert set(zone_props.keys()) == expected_ids

    # Check names
    assert zone_props["PUNE_ALANKAR_CHOWK"]["name"] == "Alankar Chowk"
    assert zone_props["PUNE_JEHANGIR_CHOWK"]["name"] == "Jehangir Chowk"
    assert zone_props["PUNE_RTO_CHOWK"]["name"] == "RTO Chowk"

    # Coordinates validation: GeoJSON Point coordinates are [longitude, latitude]
    zone_geoms = {f["properties"]["id"]: f["geometry"] for f in features}
    for zid, geom in zone_geoms.items():
        assert geom["type"] == "Point"
        coords = geom["coordinates"]
        assert len(coords) == 2
        assert isinstance(coords[0], (int, float))
        assert isinstance(coords[1], (int, float))

    # WGS84 GPS checks
    alankar_coords = zone_geoms["PUNE_ALANKAR_CHOWK"]["coordinates"]
    assert round(alankar_coords[0], 4) == 73.8741
    assert round(alankar_coords[1], 4) == 18.5284

    jehangir_coords = zone_geoms["PUNE_JEHANGIR_CHOWK"]["coordinates"]
    assert round(jehangir_coords[0], 4) == 73.8775
    assert round(jehangir_coords[1], 4) == 18.5310

    rto_coords = zone_geoms["PUNE_RTO_CHOWK"]["coordinates"]
    assert round(rto_coords[0], 4) == 73.8648
    assert round(rto_coords[1], 4) == 18.5314


# -----------------------------------------------------------------------------
# 3. Provenance Strictly 'model_estimate' & No Demo Fallback
# -----------------------------------------------------------------------------
def test_hotspots_provenance_strictly_model_estimate(client):
    """
    Verifies that all features and collection metadata carry dataSource = 'model_estimate'.
    Strictly forbids 'observed' (not ground-truth sensor data) or 'DEMO_FIXTURE'.
    """
    resp = client.get("/api/v1/hotspots")
    assert resp.status_code == 200
    data = resp.json()

    assert data["metadata"]["dataSource"] == "model_estimate"
    assert data["metadata"]["dataSource"] != "observed"
    assert data["metadata"]["dataSource"] != "DEMO_FIXTURE"

    for f in data["features"]:
        props = f["properties"]
        assert props["dataSource"] == "model_estimate"
        assert props["dataSource"] != "observed"
        assert props["dataSource"] != "DEMO_FIXTURE"


# -----------------------------------------------------------------------------
# 4. Uniform Modeled PM2.5 and AQI Across Zones
# -----------------------------------------------------------------------------
def test_hotspots_same_pm25_and_aqi_across_zones(client):
    """
    City-wide CAMS PM2.5 is identical across all 3 zones.
    AQI and CPCB band must be mutually consistent and identical across zones.
    """
    resp = client.get("/api/v1/hotspots")
    assert resp.status_code == 200
    data = resp.json()

    features = data["features"]
    pm25_values = [f["properties"]["pm25"] for f in features]
    aqi_values = [f["properties"]["aqi"] for f in features]
    band_values = [f["properties"]["aqiBand"] for f in features]

    # PM2.5 is uniform
    assert len(set(pm25_values)) == 1
    assert pm25_values[0] > 0.0

    # AQI is uniform
    assert len(set(aqi_values)) == 1
    assert len(set(band_values)) == 1

    # Verify AQI calculation formula matches canonical CPCB
    city_pm25 = pm25_values[0]
    expected_aqi = estimate_aqi_from_pm25(city_pm25)
    expected_band = get_band_from_aqi(expected_aqi)
    assert aqi_values[0] == expected_aqi
    assert band_values[0] == expected_band
    assert band_values[0] in [b.value for b in CpcbBand]


# -----------------------------------------------------------------------------
# 5. Dominant Driver & Contextual Semantics
# -----------------------------------------------------------------------------
def test_hotspots_dominant_driver_traffic(client):
    """Every feature reports dominantDriver == 'Traffic'."""
    resp = client.get("/api/v1/hotspots")
    assert resp.status_code == 200
    data = resp.json()

    for f in data["features"]:
        assert f["properties"]["dominantDriver"] == "Traffic"


# -----------------------------------------------------------------------------
# 6. Spatial Hotspot Intensity Clamped & Normalized
# -----------------------------------------------------------------------------
def test_hotspots_intensity_in_range(client):
    """Every feature intensity is strictly clamped in [0.0, 1.0]."""
    resp = client.get("/api/v1/hotspots")
    assert resp.status_code == 200
    data = resp.json()

    for f in data["features"]:
        intensity = f["properties"]["intensity"]
        assert isinstance(intensity, (int, float))
        assert 0.0 <= intensity <= 1.0


def test_hotspots_normalization_logic_with_synthetic_data(tmp_path):
    """
    Verifies min-max traffic normalization and safe 0.5 fallback on synthetic data.
    """
    # 1. Varying traffic counts: 100, 200, 300
    data_varying = {
        "timestamp": ["2023-01-18 20:00:00+05:30"] * 3,
        "zone_id": ["PUNE_ALANKAR_CHOWK", "PUNE_JEHANGIR_CHOWK", "PUNE_RTO_CHOWK"],
        "latitude": [18.5284, 18.5310, 18.5314],
        "longitude": [73.8741, 73.8775, 73.8648],
        "pm25": [75.0, 75.0, 75.0],
        "pm25_source_type": ["modeled", "modeled", "modeled"],
        "traffic_count": [100.0, 200.0, 300.0],
    }
    df_var = pd.DataFrame(data_varying)
    p_var = tmp_path / "varying.parquet"
    df_var.to_parquet(p_var)

    service_var = HotspotService(features_path=str(p_var))
    res_var = service_var.get_hotspots()
    var_map = {f.properties.id: f.properties.intensity for f in res_var.features}
    assert var_map["PUNE_ALANKAR_CHOWK"] == 0.0
    assert var_map["PUNE_JEHANGIR_CHOWK"] == 0.5
    assert var_map["PUNE_RTO_CHOWK"] == 1.0

    # 2. Equal non-zero traffic counts: fallback to 0.5
    data_equal = {
        "timestamp": ["2023-01-18 20:00:00+05:30"] * 3,
        "zone_id": ["PUNE_ALANKAR_CHOWK", "PUNE_JEHANGIR_CHOWK", "PUNE_RTO_CHOWK"],
        "latitude": [18.5284, 18.5310, 18.5314],
        "longitude": [73.8741, 73.8775, 73.8648],
        "pm25": [75.0, 75.0, 75.0],
        "pm25_source_type": ["modeled", "modeled", "modeled"],
        "traffic_count": [50.0, 50.0, 50.0],
    }
    df_eq = pd.DataFrame(data_equal)
    p_eq = tmp_path / "equal.parquet"
    df_eq.to_parquet(p_eq)

    service_eq = HotspotService(features_path=str(p_eq))
    res_eq = service_eq.get_hotspots()
    for f in res_eq.features:
        assert f.properties.intensity == 0.5


# -----------------------------------------------------------------------------
# 7. Error Handling: Missing Dataset Returns HTTP 503
# -----------------------------------------------------------------------------
def test_hotspots_missing_dataset_returns_503(client):
    """When processed feature dataset is missing, endpoint returns HTTP 503."""
    app.dependency_overrides[get_hotspot_service] = lambda: HotspotService(
        features_path="non_existent/path/aeris_features.parquet"
    )
    try:
        resp = client.get("/api/v1/hotspots")
        assert resp.status_code == 503
        data = resp.json()
        assert "missing" in data["detail"].lower()
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 8. Error Handling: No Valid Modeled PM2.5 Returns HTTP 503
# -----------------------------------------------------------------------------
def test_hotspots_no_valid_modeled_pm25_returns_503(client, tmp_path):
    """When dataset has only null or non-modeled PM2.5, endpoint returns HTTP 503."""
    data_invalid = {
        "timestamp": ["2023-01-18 20:00:00+05:30"] * 3,
        "zone_id": ["PUNE_ALANKAR_CHOWK", "PUNE_JEHANGIR_CHOWK", "PUNE_RTO_CHOWK"],
        "latitude": [18.5284, 18.5310, 18.5314],
        "longitude": [73.8741, 73.8775, 73.8648],
        "pm25": [None, None, None],
        "pm25_source_type": ["unverified", "unverified", "unverified"],
        "traffic_count": [10.0, 20.0, 30.0],
    }
    df_inv = pd.DataFrame(data_invalid)
    p_inv = tmp_path / "invalid.parquet"
    df_inv.to_parquet(p_inv)

    app.dependency_overrides[get_hotspot_service] = lambda: HotspotService(
        features_path=str(p_inv)
    )
    try:
        resp = client.get("/api/v1/hotspots")
        assert resp.status_code == 503
        data = resp.json()
        assert "no valid modeled pm2.5" in data["detail"].lower()
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 9. Error Handling: No Common Timestamp Across All Documented Zones Returns HTTP 503
# -----------------------------------------------------------------------------
def test_hotspots_no_common_timestamp_across_all_zones_returns_503(client, tmp_path):
    """
    When dataset has valid modeled PM2.5, but no single timestamp contains
    all 3 documented zones (e.g. zones are staggered across disjoint timestamps),
    the service must raise ValueError and the API must return HTTP 503.
    """
    data_disjoint = {
        "timestamp": [
            "2023-01-18 20:00:00+05:30",
            "2023-01-18 20:00:00+05:30",
            "2023-01-18 21:00:00+05:30",
        ],
        "zone_id": [
            "PUNE_ALANKAR_CHOWK",
            "PUNE_JEHANGIR_CHOWK",
            "PUNE_RTO_CHOWK",
        ],
        "latitude": [18.5284, 18.5310, 18.5314],
        "longitude": [73.8741, 73.8775, 73.8648],
        "pm25": [70.0, 70.0, 75.0],
        "pm25_source_type": ["modeled", "modeled", "modeled"],
        "traffic_count": [10.0, 20.0, 30.0],
    }
    df_disjoint = pd.DataFrame(data_disjoint)
    p_disjoint = tmp_path / "disjoint.parquet"
    df_disjoint.to_parquet(p_disjoint)

    app.dependency_overrides[get_hotspot_service] = lambda: HotspotService(
        features_path=str(p_disjoint)
    )
    try:
        resp = client.get("/api/v1/hotspots")
        assert resp.status_code == 503
        data = resp.json()
        assert (
            "no common timestamp contains valid modeled pm2.5 across all documented zones"
            in data["detail"].lower()
        )
    finally:
        app.dependency_overrides.clear()
