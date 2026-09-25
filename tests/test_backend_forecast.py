"""
Tests for AERIS ML Backend Forecast API (tests/test_backend_forecast.py)
========================================================================
Validates:
1. Preserves existing GET / and GET /health behavior.
2. Valid POST /api/v1/forecast request using a real validation row:
   - HTTP 200
   - Exact response keys: {"input_timestamp", "forecast_timestamp", "pm25_forecast", "target_source", "target_source_type"}
   - forecast_timestamp == input_timestamp + 1 hour
   - pm25_forecast is finite
   - target_source == "CAMS Global Atmospheric Composition Forecasts"
   - target_source_type == "modeled"
3. Invalid requests (missing fields or wrong types) rejected with HTTP 422.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from ml.src.features import CITY_FEATURE_COLUMNS

REPO_ROOT = Path(__file__).resolve().parent.parent
VAL_PATH = REPO_ROOT / "data" / "processed" / "aeris_ml_city_val.parquet"


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture(scope="session")
def real_validation_payload():
    """
    Constructs a valid forecast payload from a real historical validation row
    (data/processed/aeris_ml_city_val.parquet).
    Strictly NO synthetic data.
    """
    assert VAL_PATH.exists(), f"Validation dataset missing at: {VAL_PATH}"
    val_df = pd.read_parquet(VAL_PATH)
    assert not val_df.empty, "Validation dataset is empty."
    # Row 8: 08:00 AM rush hour
    row = val_df.iloc[8]

    payload = {col: float(row[col]) for col in CITY_FEATURE_COLUMNS}
    payload["input_timestamp"] = row["timestamp"].isoformat()
    return payload


# -----------------------------------------------------------------------------
# 1. Existing Endpoints Preservation
# -----------------------------------------------------------------------------
def test_root_endpoint_preserved(client):
    """Verifies existing GET / behavior is untouched."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AERIS Backend is running"}


def test_health_endpoint_preserved(client):
    """Verifies existing GET /health behavior is untouched."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# -----------------------------------------------------------------------------
# 2. POST /api/v1/forecast Endpoint Tests
# -----------------------------------------------------------------------------
def test_valid_forecast_request(client, real_validation_payload):
    """
    Sends one valid POST /api/v1/forecast request using a real row from
    data/processed/aeris_ml_city_val.parquet.

    Asserts:
    - HTTP 200
    - Exact response keys
    - forecast_timestamp == input_timestamp + 1 hour
    - pm25_forecast is finite
    - target_source == "CAMS Global Atmospheric Composition Forecasts"
    - target_source_type == "modeled"
    """
    response = client.post("/api/v1/forecast", json=real_validation_payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()

    # Exact response keys
    expected_keys = {
        "input_timestamp",
        "forecast_timestamp",
        "pm25_forecast",
        "target_source",
        "target_source_type",
    }
    assert set(data.keys()) == expected_keys, f"Response keys mismatch: {data.keys()}"

    # Target attribution and scientific labels
    assert data["target_source"] == "CAMS Global Atmospheric Composition Forecasts"
    assert data["target_source_type"] == "modeled"

    # Prediction value
    assert np.isfinite(data["pm25_forecast"])
    assert data["pm25_forecast"] == pytest.approx(67.9864, abs=1e-3)

    # 1-hour-ahead timestamp semantics
    t_in = pd.to_datetime(data["input_timestamp"])
    t_out = pd.to_datetime(data["forecast_timestamp"])
    assert t_out - t_in == pd.Timedelta(hours=1)
    assert t_out == t_in + pd.Timedelta(hours=1)


# -----------------------------------------------------------------------------
# 3. Request Validation & Error Handling
# -----------------------------------------------------------------------------
def test_forecast_missing_field_rejected(client, real_validation_payload):
    """Verifies missing feature fields are rejected by Pydantic validation with HTTP 422."""
    bad_payload = real_validation_payload.copy()
    del bad_payload["temperature"]

    response = client.post("/api/v1/forecast", json=bad_payload)
    assert response.status_code == 422


def test_forecast_missing_input_timestamp_rejected(client, real_validation_payload):
    """Verifies missing input_timestamp is rejected by Pydantic validation with HTTP 422."""
    bad_payload = real_validation_payload.copy()
    del bad_payload["input_timestamp"]

    response = client.post("/api/v1/forecast", json=bad_payload)
    assert response.status_code == 422


def test_forecast_invalid_type_rejected(client, real_validation_payload):
    """Verifies non-numeric values for numeric features are rejected with HTTP 422."""
    bad_payload = real_validation_payload.copy()
    bad_payload["traffic_total"] = "heavy_traffic"

    response = client.post("/api/v1/forecast", json=bad_payload)
    assert response.status_code == 422
