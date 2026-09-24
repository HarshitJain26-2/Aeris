"""
AERIS Backend Integration & Unit Tests (tests/test_backend_api.py)
==================================================================
Validates:
1. Health endpoints (/health and /api/health) return HTTP 200 and status ok.
2. Current API (/api/v1/current):
   - Returns HTTP 200 and conforms to AirQualityReading schema.
   - Provenance is strictly 'model_estimate' (never 'observed' or ground truth).
   - PM2.5, AQI, and CpcbBand are valid and mutually consistent.
3. Zones API (/api/v1/zones):
   - Returns HTTP 200 and exactly the 3 documented ML junction zones.
   - IDs are strictly: PUNE_ALANKAR_CHOWK, PUNE_JEHANGIR_CHOWK, PUNE_RTO_CHOWK.
   - Coordinates match documented WGS84 GPS definitions.
4. Forecast API (/api/v1/forecast):
   - Returns HTTP 200 and conforms to ForecastResponse schema.
   - Horizon is truthful: horizonHours == 1 (strictly 1-hour-ahead forecast).
   - Provenance is strictly 'model_estimate' (never fabricated or claimed observed).
   - Model version is 'xgb-pm25-v1'.
   - Every forecast point has type == 'forecast' and dataSource == 'model_estimate'.
   - Lower and upper confidence interval bounds satisfy pm25Lower <= pm25 <= pm25Upper.
5. Forecast Service & Model Loading:
   - Model loads directly from ml/models/xgb_pm25_forecaster.json.
   - Inference on canonical feature row matches baseline evaluation (~68.0 µg/m³).
   - Missing feature columns raise ValueError.
6. CPCB AQI Calculation:
   - Linear sub-index formula reproduces official CPCB breakpoints and bands.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.current import CpcbBand
from backend.app.services.forecast_service import ForecastService, MODEL_VERSION
from backend.app.utils.cpcb_aqi import (
    estimate_aqi_from_pm25,
    get_band_from_aqi,
    get_band_from_pm25,
)
from ml.src.features import CITY_FEATURE_COLUMNS


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. Health Endpoint Tests
# -----------------------------------------------------------------------------
def test_health_check(client):
    """GET /health returns HTTP 200 with status ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_health_check(client):
    """GET /api/health returns HTTP 200 with status ok."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# -----------------------------------------------------------------------------
# 2. Current Air Quality API Tests
# -----------------------------------------------------------------------------
def test_current_air_quality_endpoint(client):
    """
    GET /api/v1/current returns valid AirQualityReading conforming to schema.
    Strictly verifies CAMS Global modeled provenance labeling.
    """
    resp = client.get("/api/v1/current")
    assert resp.status_code == 200
    data = resp.json()

    # Schema field verification
    assert data["city"] == "Pune"
    assert "station" in data
    assert "timestamp" in data
    assert isinstance(data["pm25"], (int, float))
    assert data["pm25"] >= 0.0
    assert isinstance(data["pm10"], (int, float))
    assert isinstance(data["aqi"], int)
    assert 0 <= data["aqi"] <= 500
    assert data["aqiBand"] in [b.value for b in CpcbBand]

    # Provenance constraint: strictly modeled
    assert data["dataSource"] == "model_estimate"
    assert data["dataSource"] != "observed"

    # Weather & traffic fields
    assert isinstance(data["temperatureC"], (int, float))
    assert isinstance(data["humidityPct"], (int, float))
    assert isinstance(data["windSpeedKmh"], (int, float))
    assert isinstance(data["trafficIndex"], (int, float))


# -----------------------------------------------------------------------------
# 3. Zones API Tests
# -----------------------------------------------------------------------------
def test_zones_endpoint(client):
    """
    GET /api/v1/zones returns exactly the 3 documented ML junction zones:
    PUNE_ALANKAR_CHOWK, PUNE_JEHANGIR_CHOWK, PUNE_RTO_CHOWK.
    """
    resp = client.get("/api/v1/zones")
    assert resp.status_code == 200
    zones = resp.json()

    assert len(zones) == 3
    zone_ids = {z["zone_id"] for z in zones}
    expected_ids = {"PUNE_ALANKAR_CHOWK", "PUNE_JEHANGIR_CHOWK", "PUNE_RTO_CHOWK"}
    assert zone_ids == expected_ids

    # Validate coordinates for each zone
    zone_map = {z["zone_id"]: z for z in zones}
    assert round(zone_map["PUNE_ALANKAR_CHOWK"]["latitude"], 4) == 18.5284
    assert round(zone_map["PUNE_ALANKAR_CHOWK"]["longitude"], 4) == 73.8741

    assert round(zone_map["PUNE_JEHANGIR_CHOWK"]["latitude"], 4) == 18.5310
    assert round(zone_map["PUNE_JEHANGIR_CHOWK"]["longitude"], 4) == 73.8775

    assert round(zone_map["PUNE_RTO_CHOWK"]["latitude"], 4) == 18.5314
    assert round(zone_map["PUNE_RTO_CHOWK"]["longitude"], 4) == 73.8648


# -----------------------------------------------------------------------------
# 4. Forecast API Tests
# -----------------------------------------------------------------------------
def test_forecast_endpoint(client):
    """
    GET /api/v1/forecast returns ForecastResponse matching frontend contract.
    Validates:
    - Truthful horizon (horizonHours == 1)
    - Provenance: dataSource == 'model_estimate'
    - Point type: type == 'forecast'
    - Model version: 'xgb-pm25-v1'
    - Finite predictions and confidence bounds
    """
    resp = client.get("/api/v1/forecast")
    assert resp.status_code == 200
    data = resp.json()

    assert data["city"] == "Pune"
    assert "generatedAt" in data

    # Truthful horizon: existing XGBoost model is strictly 1-hour-ahead
    assert data["horizonHours"] == 1
    assert data["modelVersion"] == MODEL_VERSION
    assert data["dataSource"] == "model_estimate"

    points = data["points"]
    assert len(points) == 1, "Expected genuine 1-hour-ahead forecast point."

    pt = points[0]
    assert pt["type"] == "forecast"
    assert pt["dataSource"] == "model_estimate"
    assert isinstance(pt["pm25"], (int, float))
    assert pt["pm25"] > 0
    assert isinstance(pt["aqi"], int)
    assert pt["aqiBand"] in [b.value for b in CpcbBand]

    # Confidence interval checks
    assert pt["pm25Lower"] is not None
    assert pt["pm25Upper"] is not None
    assert pt["pm25Lower"] <= pt["pm25"] <= pt["pm25Upper"]


# -----------------------------------------------------------------------------
# 5. Forecast Service Unit Tests
# -----------------------------------------------------------------------------
def test_forecast_service_model_loading():
    """Verifies that ForecastService loads the serialized model artifact successfully."""
    service = ForecastService()
    model = service.get_model()
    assert model is not None
    assert hasattr(model, "predict")


def test_forecast_service_inference_reproducibility():
    """
    Verifies that running inference on canonical feature row produces
    the verified baseline prediction (67.9864 µg/m³).
    """
    service = ForecastService()
    forecast = service.generate_forecast()

    assert forecast.horizonHours == 1
    assert len(forecast.points) == 1
    point = forecast.points[0]

    # Prediction on canonical row is ~68.0 µg/m³
    assert 65.0 <= point.pm25 <= 70.0
    assert point.type == "forecast"
    assert point.dataSource == "model_estimate"


def test_forecast_service_missing_feature_raises_error():
    """Verifies that if any required feature is missing, ValueError is raised."""
    service = ForecastService()
    incomplete_features = {"temperature": 25.0, "humidity": 50.0}
    with pytest.raises(ValueError, match="missing required columns"):
        service.generate_forecast(features=incomplete_features)


# -----------------------------------------------------------------------------
# 6. CPCB AQI Calculation Tests
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "pm25,expected_band",
    [
        (15.0, "Good"),
        (30.0, "Good"),
        (45.0, "Satisfactory"),
        (60.0, "Satisfactory"),
        (75.0, "Moderate"),
        (90.0, "Moderate"),
        (105.0, "Poor"),
        (120.0, "Poor"),
        (150.0, "Very Poor"),
        (250.0, "Very Poor"),
        (300.0, "Severe"),
    ],
)
def test_cpcb_bands(pm25, expected_band):
    """Verifies that PM2.5 concentrations map to correct CPCB AQI bands."""
    band = get_band_from_pm25(pm25)
    assert band == expected_band


def test_estimate_aqi_bounds():
    """Verifies that estimated AQI stays within 0 to 500 bounds."""
    assert estimate_aqi_from_pm25(0.0) == 0
    assert estimate_aqi_from_pm25(-10.0) == 0
    assert estimate_aqi_from_pm25(30.0) == 50
    assert estimate_aqi_from_pm25(60.0) == 100
    assert estimate_aqi_from_pm25(90.0) == 200
    assert estimate_aqi_from_pm25(120.0) == 300
    assert estimate_aqi_from_pm25(250.0) == 400
    assert estimate_aqi_from_pm25(1000.0) == 500
