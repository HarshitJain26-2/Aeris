"""
Scenario Simulation API Integration & Unit Tests (tests/test_scenario_api.py)
=============================================================================
Validates:
1. 0% reduction: scenario_pm25 equals baseline_pm25 within tolerance, delta == 0.0.
2. 30% reduction: uses real scenario engine and returns verified model result.
3. 50% reduction: uses real scenario engine and returns non-monotonic model result (delta == 0.3199).
4. -1% reduction: strictly rejected with HTTP 422 (Pydantic validation).
5. 101% reduction: strictly rejected with HTTP 422 (Pydantic validation).
6. Non-numeric reduction: strictly rejected with HTTP 422.
7. Response schema: conforms to required typed response including baseline_pm25, scenario_pm25, delta.
8. Provenance: strictly labeled as 'model_estimate' (never 'observed' or ground truth).
9. Real scenario calculation: model-driven inference, not a fake or hardcoded formula.
10. Frontend contract compatibility: provides snapshots and accepts trafficReductionPct alias.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.current import CpcbBand
from backend.app.services.scenario_service import ScenarioService


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. 0% Reduction (Identity Baseline)
# -----------------------------------------------------------------------------
def test_scenario_zero_percent_reduction(client):
    """
    POST /api/scenario/simulate with 0% reduction:
    scenario_pm25 must equal baseline_pm25 within normal floating point tolerance,
    and delta must be 0.0.
    """
    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 0})
    assert resp.status_code == 200
    data = resp.json()

    assert data["traffic_reduction_pct"] == 0.0
    assert data["baseline_pm25"] == pytest.approx(data["scenario_pm25"], abs=1e-4)
    assert data["delta"] == 0.0
    assert data["percent_change"] == 0.0
    assert data["dataSource"] == "model_estimate"


# -----------------------------------------------------------------------------
# 2. 30% Reduction
# -----------------------------------------------------------------------------
def test_scenario_thirty_percent_reduction(client):
    """
    POST /api/scenario/simulate with 30% reduction:
    Uses the actual scenario engine and model context.
    Delta is calculated as scenario_pm25 - baseline_pm25.
    """
    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 30})
    assert resp.status_code == 200
    data = resp.json()

    assert data["traffic_reduction_pct"] == 30.0
    assert isinstance(data["baseline_pm25"], (int, float))
    assert isinstance(data["scenario_pm25"], (int, float))
    assert data["delta"] == pytest.approx(data["scenario_pm25"] - data["baseline_pm25"], abs=1e-4)
    assert data["dataSource"] == "model_estimate"
    assert "traffic_total" in data["modified_features"]
    assert data["modified_features"]["traffic_total"]["factor"] == pytest.approx(0.7, abs=1e-4)


# -----------------------------------------------------------------------------
# 3. 50% Reduction
# -----------------------------------------------------------------------------
def test_scenario_fifty_percent_reduction(client):
    """
    POST /api/scenario/simulate with 50% reduction:
    Uses the actual XGBoost model result and reports non-monotonic effect honestly.
    Matches verified sensitivity artifact (baseline ~67.9864, scenario ~68.3063, delta ~0.3199).
    """
    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 50})
    assert resp.status_code == 200
    data = resp.json()

    assert data["traffic_reduction_pct"] == 50.0
    assert data["baseline_pm25"] == pytest.approx(67.9864, rel=1e-3)
    assert data["scenario_pm25"] == pytest.approx(68.3063, rel=1e-3)
    assert data["delta"] == pytest.approx(0.3199, rel=1e-3)
    assert data["delta"] == pytest.approx(data["scenario_pm25"] - data["baseline_pm25"], abs=1e-4)
    assert data["dataSource"] == "model_estimate"


# -----------------------------------------------------------------------------
# 4. Negative Percentage Rejection (-1%)
# -----------------------------------------------------------------------------
def test_scenario_negative_percent_rejected(client):
    """Negative traffic reduction percentages must be strictly rejected with HTTP 422."""
    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": -1.0})
    assert resp.status_code == 422
    err_detail = resp.json().get("detail", [])
    assert any("traffic_reduction_pct" in str(err) for err in err_detail)


# -----------------------------------------------------------------------------
# 5. Boundary Validation: 50% accepted, 51% rejected, 100% rejected
# -----------------------------------------------------------------------------
def test_scenario_boundary_50_accepted_51_and_100_rejected(client):
    """
    Confirms the 0-50% contract:
    - 50% -> accepted (HTTP 200)
    - 51% -> rejected (HTTP 422)
    - 100% -> rejected (HTTP 422)
    """
    # 50% is accepted
    resp_50 = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 50})
    assert resp_50.status_code == 200
    assert resp_50.json()["traffic_reduction_pct"] == 50.0

    # 51% is rejected
    resp_51 = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 51})
    assert resp_51.status_code == 422
    err_51 = resp_51.json().get("detail", [])
    assert any("traffic_reduction_pct" in str(err) for err in err_51)

    # 100% is rejected
    resp_100 = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 100})
    assert resp_100.status_code == 422
    err_100 = resp_100.json().get("detail", [])
    assert any("traffic_reduction_pct" in str(err) for err in err_100)


def test_scenario_greater_than_100_percent_rejected(client):
    """Traffic reduction percentages > 100 must be strictly rejected with HTTP 422."""
    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 101.0})
    assert resp.status_code == 422
    err_detail = resp.json().get("detail", [])
    assert any("traffic_reduction_pct" in str(err) for err in err_detail)


# -----------------------------------------------------------------------------
# 6. Non-Numeric Rejection
# -----------------------------------------------------------------------------
def test_scenario_non_numeric_rejected(client):
    """Non-numeric traffic reduction values must be strictly rejected with HTTP 422."""
    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": "thirty_percent"})
    assert resp.status_code == 422


# -----------------------------------------------------------------------------
# 7. Response Schema Validation
# -----------------------------------------------------------------------------
def test_scenario_response_schema(client):
    """
    Verifies that POST /api/scenario/simulate returns complete typed schema:
    - baseline_pm25, scenario_pm25, delta, traffic_reduction_pct, dataSource
    - scientific disclaimer
    - frontend-compatible snapshots (baseline, modelled, input, deltaAbsolute, deltaPct)
    """
    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 25.0})
    assert resp.status_code == 200
    data = resp.json()

    # Core required fields
    required_fields = [
        "baseline_pm25",
        "scenario_pm25",
        "delta",
        "traffic_reduction_pct",
        "dataSource",
        "data_source",
        "percent_change",
        "disclaimer",
        "modified_features",
        "baseline",
        "modelled",
        "input",
        "deltaAbsolute",
        "deltaPct",
        "method",
        "isModelEstimate",
    ]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Scientific disclaimer text verification
    assert "predictive rather than causal" in data["disclaimer"]
    assert "non-monotonic" in data["disclaimer"]

    # AQI snapshot schema verification
    for snap_key in ["baseline", "modelled"]:
        snap = data[snap_key]
        assert isinstance(snap["pm25"], (int, float))
        assert isinstance(snap["aqi"], int)
        assert snap["aqiBand"] in [b.value for b in CpcbBand]


# -----------------------------------------------------------------------------
# 8. Provenance Validation
# -----------------------------------------------------------------------------
def test_scenario_provenance(client):
    """
    Verifies that provenance is strictly labeled as 'model_estimate'
    and never claims to be 'observed' or ground truth.
    """
    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 30})
    assert resp.status_code == 200
    data = resp.json()

    assert data["dataSource"] == "model_estimate"
    assert data["dataSource"] != "observed"
    assert data["isModelEstimate"] is True
    assert data["method"] == "backend-solver"


# -----------------------------------------------------------------------------
# 9. Real Scenario Calculation (Dynamic Inference, Not Hardcoded)
# -----------------------------------------------------------------------------
def test_scenario_real_calculation(client):
    """
    Verifies that the endpoint executes actual ML model inference
    and correctly reflects the dynamic feature modifications.
    """
    service = ScenarioService()
    model = service.get_model()
    assert model is not None

    resp = client.post("/api/scenario/simulate", json={"traffic_reduction_pct": 50})
    data = resp.json()

    # Baseline matches canonical model evaluation
    assert 65.0 <= data["baseline_pm25"] <= 70.0
    # Modified traffic feature counts match factor 0.5
    mod = data["modified_features"]
    assert mod["traffic_total"]["scenario"] == pytest.approx(mod["traffic_total"]["baseline"] * 0.5, rel=1e-4)


# -----------------------------------------------------------------------------
# 10. Frontend Contract & Alias Compatibility
# -----------------------------------------------------------------------------
def test_scenario_alias_and_v1_route_compatibility(client):
    """
    Verifies that:
    1. Request accepts camelCase 'trafficReductionPct' alias.
    2. POST /api/v1/scenario/simulate also resolves identically.
    """
    # Test camelCase alias
    resp_alias = client.post("/api/scenario/simulate", json={"trafficReductionPct": 30})
    assert resp_alias.status_code == 200
    assert resp_alias.json()["traffic_reduction_pct"] == 30.0

    # Test /api/v1/scenario/simulate route
    resp_v1 = client.post("/api/v1/scenario/simulate", json={"traffic_reduction_pct": 30})
    assert resp_v1.status_code == 200
    assert resp_v1.json()["traffic_reduction_pct"] == 30.0


# -----------------------------------------------------------------------------
# 11. Canonical Evaluation Context Verification
# -----------------------------------------------------------------------------
def test_default_scenario_context_uses_verified_evaluation_hour():
    """
    Verifies that default ScenarioService context uses the verified canonical
    evaluation hour (2023-01-18 08:00:00+05:30) rather than the 22:00 validation row.
    """
    from backend.app.repositories.forecast_repository import ForecastRepository
    from backend.app.services.scenario_service import ScenarioService

    repo = ForecastRepository()
    canonical_feat = repo.get_verified_evaluation_feature_vector()
    assert canonical_feat["timestamp"] == "2023-01-18 08:00:00+05:30"

    # Ensure it differs from the last row (22:00) of validation parquet
    latest_feat = repo.get_latest_feature_vector()
    assert latest_feat["timestamp"] != canonical_feat["timestamp"]
    assert "22:00" in latest_feat["timestamp"]

    # Verify simulate default context produces the verified model-driven results
    service = ScenarioService(forecast_repo=repo)
    res = service.simulate(traffic_reduction_pct=50.0)
    assert res.baseline_pm25 == pytest.approx(67.9864, rel=1e-3)
    assert res.scenario_pm25 == pytest.approx(68.3063, rel=1e-3)
    assert res.delta == pytest.approx(0.3199, rel=1e-3)
