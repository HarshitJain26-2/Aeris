"""
Tests for AERIS ML Inference Layer (tests/test_inference.py)
============================================================
Validates:
1. Model loads successfully from default path and explicit path.
2. Valid feature vector predicts finite value.
3. Missing feature rejected (ValueError / KeyError).
4. Wrong feature order rejected (ValueError).
5. NaN/inf/None/bool/string features rejected (ValueError).
6. Counterfactual 0% identity (baseline == scenario, delta == 0.0).
7. Invalid reduction percentage rejected (outside 0-50: ValueError; non-numeric: TypeError).
8. Output schema stability for both prediction and counterfactual.
9. 1-hour-ahead timestamp semantics: forecast_timestamp == input_timestamp + 1 hour.
10. Trained model file is strictly unchanged (SHA256 checksum).
11. Input type validation (rejects unsupported types and multi-row DataFrames).
"""

import hashlib
import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import xgboost as xgb

from ml.src.features import CITY_FEATURE_COLUMNS
from ml.src.inference import (
    DEFAULT_MODEL_PATH,
    MissingFeatureError,
    load_forecaster,
    predict_next_hour,
    run_traffic_counterfactual,
    validate_features,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
VAL_PATH = REPO_ROOT / "data" / "processed" / "aeris_ml_city_val.parquet"
MODEL_PATH = REPO_ROOT / "ml" / "models" / "xgb_pm25_forecaster.json"

# SHA256 checksum of ml/models/xgb_pm25_forecaster.json
EXPECTED_MODEL_SHA256 = "35f9a649623bac0981f00b472cefb823ca7aade8675a8556a7b55364faa17377"


@pytest.fixture(scope="session")
def real_validation_row():
    """
    Test fixture loading an actual historical validation row from aeris_ml_city_val.parquet.
    Strictly uses real data; NO synthetic data generation.
    """
    if not VAL_PATH.exists():
        pytest.fail(f"Real validation dataset missing at: {VAL_PATH}")
    val_df = pd.read_parquet(VAL_PATH)
    assert not val_df.empty, "Validation dataset is empty."
    # Use hour 8 (08:00 AM rush hour)
    return val_df.iloc[8]


@pytest.fixture(scope="session")
def loaded_model():
    """Loads and caches model once for test session."""
    return load_forecaster()


# -----------------------------------------------------------------------------
# 1. Model Loading Tests
# -----------------------------------------------------------------------------
def test_model_loads_successfully():
    """Verifies that load_forecaster loads model from default and explicit paths."""
    # Default path
    model = load_forecaster()
    assert isinstance(model, xgb.XGBRegressor)
    assert model._Booster is not None

    # Explicit path
    model_exp = load_forecaster(str(MODEL_PATH))
    assert isinstance(model_exp, xgb.XGBRegressor)

    # Non-existent path raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        load_forecaster("ml/models/non_existent_model.json")


# -----------------------------------------------------------------------------
# 2. Valid Feature Vector Predicts Finite Value
# -----------------------------------------------------------------------------
def test_valid_feature_vector_predicts_finite_value(real_validation_row, loaded_model):
    """Verifies that a valid feature vector produces a finite forecast across Series, DataFrame, and dict."""
    # pd.Series input
    res_series = predict_next_hour(real_validation_row, model=loaded_model)
    assert np.isfinite(res_series["pm25_forecast"])
    assert res_series["pm25_forecast"] > 0

    # pd.DataFrame input
    df_row = pd.DataFrame([real_validation_row.to_dict()])
    res_df = predict_next_hour(df_row, model=loaded_model)
    assert np.isfinite(res_df["pm25_forecast"])

    # dict input (with exactly CITY_FEATURE_COLUMNS in order)
    dict_row = {c: float(real_validation_row[c]) for c in CITY_FEATURE_COLUMNS}
    res_dict = predict_next_hour(dict_row, model=loaded_model)
    assert np.isfinite(res_dict["pm25_forecast"])

    # Consistent prediction across all 3 input formats
    assert res_series["pm25_forecast"] == res_df["pm25_forecast"]
    assert res_series["pm25_forecast"] == res_dict["pm25_forecast"]


# -----------------------------------------------------------------------------
# 3. Missing Feature Rejected
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("missing_col", [
    "temperature",
    "humidity",
    "traffic_total",
    "pm25_lag_1h",
    "traffic_x_wind",
])
def test_missing_feature_rejected(real_validation_row, missing_col, loaded_model):
    """Verifies that dropping any required feature is rejected with ValueError/KeyError."""
    # Test on dict
    row_dict = {c: real_validation_row[c] for c in CITY_FEATURE_COLUMNS if c != missing_col}
    with pytest.raises((ValueError, KeyError)):
        predict_next_hour(row_dict, model=loaded_model)

    with pytest.raises((ValueError, KeyError)):
        run_traffic_counterfactual(row_dict, reduction_pct=25.0, model=loaded_model)

    # Test on DataFrame
    df_row = pd.DataFrame([real_validation_row.to_dict()]).drop(columns=[missing_col])
    with pytest.raises((ValueError, KeyError)):
        predict_next_hour(df_row, model=loaded_model)

    with pytest.raises((ValueError, KeyError)):
        run_traffic_counterfactual(df_row, reduction_pct=25.0, model=loaded_model)


# -----------------------------------------------------------------------------
# 4. Wrong Feature Order Rejected
# -----------------------------------------------------------------------------
def test_wrong_feature_order_rejected(real_validation_row, loaded_model):
    """Verifies that features presented in incorrect column order are strictly rejected."""
    # 1. Reverse the entire feature schema
    reversed_cols = list(reversed(CITY_FEATURE_COLUMNS))
    reversed_dict = {c: real_validation_row[c] for c in reversed_cols}
    with pytest.raises(ValueError, match="Incorrect feature ordering"):
        predict_next_hour(reversed_dict, model=loaded_model)

    with pytest.raises(ValueError, match="Incorrect feature ordering"):
        run_traffic_counterfactual(reversed_dict, reduction_pct=25.0, model=loaded_model)

    # 2. Swap two adjacent features (temperature and humidity)
    swapped_cols = list(CITY_FEATURE_COLUMNS)
    swapped_cols[0], swapped_cols[1] = swapped_cols[1], swapped_cols[0]
    swapped_df = pd.DataFrame([real_validation_row.to_dict()])[swapped_cols]

    with pytest.raises(ValueError, match="Incorrect feature ordering"):
        predict_next_hour(swapped_df, model=loaded_model)

    with pytest.raises(ValueError, match="Incorrect feature ordering"):
        run_traffic_counterfactual(swapped_df, reduction_pct=25.0, model=loaded_model)

    # 3. Series with scrambled index
    scrambled_series = real_validation_row[swapped_cols]
    with pytest.raises(ValueError, match="Incorrect feature ordering"):
        predict_next_hour(scrambled_series, model=loaded_model)


# -----------------------------------------------------------------------------
# 5. NaN / Inf / None / Invalid Values Rejected
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("invalid_val", [
    np.nan,
    float("nan"),
    float("inf"),
    float("-inf"),
    None,
    "unmeasured",
    True,
])
def test_nan_inf_rejected(real_validation_row, invalid_val, loaded_model):
    """Verifies that NaN, Inf, None, bool, and string feature values are strictly rejected."""
    # Test invalid value on a continuous feature (wind_speed)
    bad_dict = {c: real_validation_row[c] for c in CITY_FEATURE_COLUMNS}
    bad_dict["wind_speed"] = invalid_val

    with pytest.raises(ValueError):
        predict_next_hour(bad_dict, model=loaded_model)

    with pytest.raises(ValueError):
        run_traffic_counterfactual(bad_dict, reduction_pct=25.0, model=loaded_model)


# -----------------------------------------------------------------------------
# 6. Counterfactual 0% Identity
# -----------------------------------------------------------------------------
def test_counterfactual_zero_percent_identity(real_validation_row, loaded_model):
    """0% reduction must yield identical baseline and scenario predictions (delta = 0.0)."""
    for pct in [0, 0.0]:
        res = run_traffic_counterfactual(real_validation_row, reduction_pct=pct, model=loaded_model)
        assert res["baseline_pm25"] == res["scenario_pm25"]
        assert res["delta_pm25"] == 0.0
        assert res["reduction_pct"] == 0.0

        # Baseline must match standalone predict_next_hour
        pred_res = predict_next_hour(real_validation_row, model=loaded_model)
        assert res["baseline_pm25"] == pred_res["pm25_forecast"]


# -----------------------------------------------------------------------------
# 7. Invalid Reduction Rejected
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("invalid_pct", [-0.1, -10.0, 50.01, 75.0, 100.0])
def test_invalid_reduction_percentage_value_rejected(real_validation_row, invalid_pct, loaded_model):
    """Reduction percentages outside 0 to 50 must raise ValueError."""
    with pytest.raises(ValueError, match="between 0 and 50"):
        run_traffic_counterfactual(real_validation_row, reduction_pct=invalid_pct, model=loaded_model)


@pytest.mark.parametrize("bad_type_pct", ["25", True, False, None, [25.0]])
def test_invalid_reduction_percentage_type_rejected(real_validation_row, bad_type_pct, loaded_model):
    """Non-numeric reduction percentage types must raise TypeError."""
    with pytest.raises(TypeError, match="must be numeric"):
        run_traffic_counterfactual(real_validation_row, reduction_pct=bad_type_pct, model=loaded_model)


# -----------------------------------------------------------------------------
# 8. Output Schema Stability & 1-Hour-Ahead Timestamp Semantics
# -----------------------------------------------------------------------------
def test_prediction_output_schema_stable(real_validation_row, loaded_model):
    """Verifies predict_next_hour produces exact dictionary schema with input and forecast timestamps."""
    res = predict_next_hour(real_validation_row, model=loaded_model)

    expected_keys = {
        "input_timestamp",
        "forecast_timestamp",
        "pm25_forecast",
        "target_source",
        "target_source_type",
    }
    assert set(res.keys()) == expected_keys
    assert res["target_source"] == "CAMS Global Atmospheric Composition Forecasts"
    assert res["target_source_type"] == "modeled"
    assert isinstance(res["input_timestamp"], str)
    assert isinstance(res["forecast_timestamp"], str)
    assert isinstance(res["pm25_forecast"], float)

    # 1-hour-ahead semantics check
    t_in = pd.to_datetime(res["input_timestamp"])
    t_out = pd.to_datetime(res["forecast_timestamp"])
    assert t_out == t_in + pd.Timedelta(hours=1)


def test_counterfactual_output_schema_stable(real_validation_row, loaded_model):
    """Verifies run_traffic_counterfactual produces exact dictionary schema with input and forecast timestamps."""
    res = run_traffic_counterfactual(real_validation_row, reduction_pct=25.0, model=loaded_model)

    expected_keys = {
        "input_timestamp",
        "forecast_timestamp",
        "baseline_pm25",
        "scenario_pm25",
        "delta_pm25",
        "reduction_pct",
        "scenario_type",
    }
    assert set(res.keys()) == expected_keys
    assert res["scenario_type"] == "modeled traffic-reduction scenario"
    assert isinstance(res["input_timestamp"], str)
    assert isinstance(res["forecast_timestamp"], str)
    assert isinstance(res["baseline_pm25"], float)
    assert isinstance(res["scenario_pm25"], float)
    assert isinstance(res["delta_pm25"], float)
    assert isinstance(res["reduction_pct"], float)
    assert res["reduction_pct"] == 25.0

    # 1-hour-ahead semantics check
    t_in = pd.to_datetime(res["input_timestamp"])
    t_out = pd.to_datetime(res["forecast_timestamp"])
    assert t_out == t_in + pd.Timedelta(hours=1)


def test_one_hour_ahead_timestamp_semantics(real_validation_row, loaded_model):
    """
    Explicitly tests:
    forecast_timestamp == input_timestamp + 1 hour.
    Input features at timestamp t predict target at t + 1 hour.
    """
    # Prediction
    pred = predict_next_hour(real_validation_row, model=loaded_model)
    dt_in = pd.to_datetime(pred["input_timestamp"])
    dt_fc = pd.to_datetime(pred["forecast_timestamp"])
    assert dt_fc - dt_in == pd.Timedelta(hours=1)
    assert dt_fc == dt_in + pd.Timedelta(hours=1)

    # Counterfactual
    scen = run_traffic_counterfactual(real_validation_row, reduction_pct=25.0, model=loaded_model)
    dt_scen_in = pd.to_datetime(scen["input_timestamp"])
    dt_scen_fc = pd.to_datetime(scen["forecast_timestamp"])
    assert dt_scen_fc - dt_scen_in == pd.Timedelta(hours=1)
    assert dt_scen_fc == dt_scen_in + pd.Timedelta(hours=1)


# -----------------------------------------------------------------------------
# 9. Trained Model File is Unchanged
# -----------------------------------------------------------------------------
def test_trained_model_file_is_unchanged():
    """Guarantees that model weights file xgb_pm25_forecaster.json has not been modified or retrained."""
    assert MODEL_PATH.exists(), f"Model file missing: {MODEL_PATH}"
    with open(MODEL_PATH, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    assert file_hash.lower() == EXPECTED_MODEL_SHA256.lower(), (
        f"Model file checksum altered! Expected {EXPECTED_MODEL_SHA256}, got {file_hash}."
    )


# -----------------------------------------------------------------------------
# 10. Unsupported Inputs & Multi-row DataFrames Rejected
# -----------------------------------------------------------------------------
def test_unsupported_input_type_rejected(loaded_model):
    """Lists, arrays, or scalars passed as features must raise TypeError."""
    with pytest.raises(TypeError, match="Unsupported features type"):
        predict_next_hour([1.0, 2.0, 3.0], model=loaded_model)

    with pytest.raises(TypeError, match="Unsupported features type"):
        run_traffic_counterfactual(42, reduction_pct=20.0, model=loaded_model)


def test_multi_row_dataframe_rejected(real_validation_row, loaded_model):
    """DataFrames with more than 1 row must raise ValueError."""
    two_row_df = pd.DataFrame([real_validation_row.to_dict(), real_validation_row.to_dict()])
    with pytest.raises(ValueError, match="must contain exactly 1 row"):
        predict_next_hour(two_row_df, model=loaded_model)

    with pytest.raises(ValueError, match="must contain exactly 1 row"):
        run_traffic_counterfactual(two_row_df, reduction_pct=20.0, model=loaded_model)
