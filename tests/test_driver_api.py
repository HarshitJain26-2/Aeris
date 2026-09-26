"""
AERIS Driver Attribution API Tests (tests/test_driver_api.py)
=============================================================
Validates:
1. GET /api/v1/drivers returns HTTP 200.
2. Exact top-level response keys ("city", "period", "drivers", "method", "disclaimer", "dataSource").
3. Exactly 4 driver categories.
4. Categories exactly match:
   - "Recent PM2.5 history"
   - "Weather"
   - "Traffic"
   - "Time / calendar"
5. dataSource == "model_estimate".
6. method == "model_feature_attribution".
7. estimatedPct values are finite and non-negative.
8. Sum of estimatedPct is exactly 100.00 (within floating point precision).
9. Values are dynamically derived from ml/evaluation/shap_importance.csv, not hardcoded.
10. No category is Industrial or Residential/Biomass.
11. Full response conforms strictly to frontend/src/types/source.ts contract.
"""

import csv
import math
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.drivers import DriverAttributionResponse
from backend.app.services.driver_service import (
    DriverService,
    DRIVER_GROUPS,
    DRIVER_DESCRIPTIONS,
    DISCLAIMER_TEXT,
)


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


EXPECTED_TOP_LEVEL_KEYS = {
    "city",
    "period",
    "drivers",
    "method",
    "disclaimer",
    "dataSource",
}

EXPECTED_DRIVER_KEYS = {
    "category",
    "estimatedPct",
    "ciLower",
    "ciUpper",
    "description",
}

EXPECTED_CATEGORIES = [
    "Recent PM2.5 history",
    "Weather",
    "Traffic",
    "Time / calendar",
]


def test_get_drivers_returns_200(client):
    """1. GET /api/v1/drivers returns HTTP 200."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200


def test_exact_top_level_response_keys(client):
    """2. Exact top-level response keys."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == EXPECTED_TOP_LEVEL_KEYS
    assert data["city"] == "Pune"
    assert data["period"] == "validation holdout — model feature attribution"


def test_exactly_four_driver_categories(client):
    """3. Exactly 4 driver categories."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["drivers"]) == 4


def test_categories_match_four_model_driver_groups(client):
    """4. Categories exactly match the four model-driver groups in deterministic order."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()
    actual_categories = [d["category"] for d in data["drivers"]]
    assert actual_categories == EXPECTED_CATEGORIES


def test_data_source_is_model_estimate(client):
    """5. dataSource == 'model_estimate' (never observed or fixture in production)."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()
    assert data["dataSource"] == "model_estimate"


def test_method_is_model_feature_attribution(client):
    """6. method == 'model_feature_attribution'."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "model_feature_attribution"
    assert data["disclaimer"] == DISCLAIMER_TEXT


def test_estimated_pct_finite_and_non_negative(client):
    """7. estimatedPct values are finite and non-negative; ci fields equal estimatedPct."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()

    for item in data["drivers"]:
        pct = item["estimatedPct"]
        assert isinstance(pct, (int, float))
        assert math.isfinite(pct)
        assert pct >= 0.0

        # ciLower and ciUpper must equal estimatedPct (not fabricated confidence intervals)
        assert item["ciLower"] == pct
        assert item["ciUpper"] == pct


def test_sum_of_estimated_pct_is_100(client):
    """8. Sum of estimatedPct is approximately 100 (exactly 100.0 after rounding logic)."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()
    total_pct = sum(d["estimatedPct"] for d in data["drivers"])
    assert round(total_pct, 2) == 100.00


def test_values_derived_from_shap_artifact_not_hardcoded(client, tmp_path):
    """
    9. Values are dynamically derived from ml/evaluation/shap_importance.csv,
    not hardcoded.
    """
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()

    # Read shap_importance.csv directly and compute expected values independently
    csv_path = Path("ml/evaluation/shap_importance.csv")
    assert csv_path.exists(), "SHAP importance artifact must exist"

    raw_data = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_data[row["feature"].strip()] = float(row["mean_abs_shap"].strip())

    group_sums = {
        cat: sum(raw_data.get(feat, 0.0) for feat in feats)
        for cat, feats in DRIVER_GROUPS.items()
    }
    total = sum(group_sums.values())
    raw_pcts = {cat: (s / total) * 100.0 for cat, s in group_sums.items()}
    expected_rounded = {cat: round(p, 2) for cat, p in raw_pcts.items()}
    sum_rounded = round(sum(expected_rounded.values()), 2)
    diff = round(100.0 - sum_rounded, 2)
    if abs(diff) > 1e-6:
        largest = max(expected_rounded.keys(), key=lambda k: (expected_rounded[k], k))
        expected_rounded[largest] = round(expected_rounded[largest] + diff, 2)

    api_pcts = {d["category"]: d["estimatedPct"] for d in data["drivers"]}
    assert api_pcts == expected_rounded

    # Test dynamic sensitivity: using a custom artifact produces different numbers
    custom_csv = tmp_path / "custom_shap.csv"
    with open(custom_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["feature", "mean_abs_shap"])
        writer.writerow(["pm25_lag_1h", "10.0"])
        writer.writerow(["temperature", "10.0"])
        writer.writerow(["traffic_total", "10.0"])
        writer.writerow(["hour_of_day", "10.0"])

    service = DriverService(shap_path=str(custom_csv))
    custom_result = service.compute_attribution()
    custom_pcts = {d.category: d.estimatedPct for d in custom_result.drivers}
    assert custom_pcts == {
        "Recent PM2.5 history": 25.0,
        "Weather": 25.0,
        "Traffic": 25.0,
        "Time / calendar": 25.0,
    }
    assert custom_pcts != api_pcts


def test_no_industrial_or_residential_categories(client):
    """10. No category is Industrial or Residential/Biomass."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()
    categories = {d["category"] for d in data["drivers"]}
    assert "Industrial" not in categories
    assert "Residential/Biomass" not in categories
    assert "Residential" not in categories
    assert "Biomass" not in categories


def test_full_response_contract_compatibility(client):
    """11. Full response is compatible with frontend/src/types/source.ts."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    data = response.json()

    # Validates through Pydantic schema
    validated = DriverAttributionResponse.model_validate(data)
    assert validated.city == "Pune"
    assert validated.method == "model_feature_attribution"
    assert validated.dataSource == "model_estimate"
    assert len(validated.drivers) == 4

    for driver in validated.drivers:
        assert driver.category in EXPECTED_CATEGORIES
        assert isinstance(driver.estimatedPct, float)
        assert isinstance(driver.ciLower, float)
        assert isinstance(driver.ciUpper, float)
        assert driver.ciLower == driver.estimatedPct
        assert driver.ciUpper == driver.estimatedPct
        assert driver.description == DRIVER_DESCRIPTIONS[driver.category]
