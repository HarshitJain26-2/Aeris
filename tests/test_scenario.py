"""
Tests for AERIS Counterfactual Scenario Engine (tests/test_scenario.py)
=======================================================================
Validates:
1. 0% reduction produces identical baseline and scenario predictions (identity).
2. Standard reduction percentages (5%, 10%, 25%, 50%) are accepted.
3. Reduction percentages > 50% are strictly rejected with ValueError.
4. Negative reduction percentages are strictly rejected with ValueError.
5. Non-numeric reduction percentages are rejected with TypeError.
6. Weather features remain strictly unchanged.
7. PM2.5 lags and historical rolling averages remain strictly unchanged.
8. Only traffic-dependent features are modified.
9. Scenario prediction output is finite.
10. Feature ordering passed to model exactly matches CITY_FEATURE_COLUMNS.
11. Works with pd.Series, single-row pd.DataFrame, and dictionary inputs.
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from ml.src.features import CITY_FEATURE_COLUMNS
from ml.src.scenario import (
    CURRENT_HOUR_TRAFFIC_FEATURES,
    UNMODIFIED_FEATURES,
    run_traffic_reduction_scenario,
)


class MockXGBModel:
    """Mock model that records the feature columns it received and computes a linear dummy."""
    def __init__(self):
        self.last_features_seen = None

    def predict(self, X):
        if isinstance(X, pd.DataFrame):
            self.last_features_seen = list(X.columns)
            # Simple linear combination for testing
            return 50.0 + 0.05 * X["traffic_total"].values - 0.2 * X["temperature"].values
        return np.array([50.0])


@pytest.fixture
def sample_feature_row():
    """Generates a complete, valid sample feature row matching the 25-feature schema."""
    row = {
        "timestamp": "2023-01-18 08:00:00+05:30",
        "temperature": 17.4,
        "humidity": 65.0,
        "wind_speed": 3.6,
        "rainfall": 0.0,
        "traffic_alankar": 7.0,
        "traffic_jehangir": 20.0,
        "traffic_rto": 13.0,
        "traffic_total": 40.0,
        "hour_of_day": 8,
        "day_of_week": 2,
        "is_weekend": 0,
        "pm25_lag_1h": 102.4,
        "pm25_lag_2h": 96.6,
        "pm25_lag_3h": 91.5,
        "pm25_lag_6h": 82.4,
        "pm25_lag_12h": 51.8,
        "pm25_lag_24h": 115.7,
        "pm25_roll_mean_3h": 96.83,
        "pm25_roll_mean_6h": 91.57,
        "pm25_roll_mean_12h": 78.81,
        "pm25_roll_mean_24h": 63.87,
        "traffic_roll_mean_3h": 13.33,
        "traffic_roll_mean_6h": 6.67,
        "traffic_x_wind": 144.0,
        "traffic_x_humidity": 2600.0,
    }
    return pd.Series(row)


def test_zero_percent_identity(sample_feature_row):
    """0% reduction must yield identical baseline and scenario predictions (delta = 0.0)."""
    mock_model = MockXGBModel()
    res = run_traffic_reduction_scenario(sample_feature_row, reduction_pct=0, model=mock_model)
    assert res["baseline_prediction"] == res["scenario_prediction"]
    assert res["delta_pm25"] == 0.0
    assert res["percent_change"] == 0.0


@pytest.mark.parametrize("pct", [5, 10, 25, 50, 5.5, 49.9])
def test_valid_percentages_accepted(sample_feature_row, pct):
    """5%, 10%, 25%, 50% and valid floats must be accepted."""
    mock_model = MockXGBModel()
    res = run_traffic_reduction_scenario(sample_feature_row, reduction_pct=pct, model=mock_model)
    assert res["reduction_pct"] == pct
    assert np.isfinite(res["scenario_prediction"])


def test_greater_than_fifty_percent_rejected(sample_feature_row):
    """Reduction > 50% must be strictly rejected with ValueError."""
    mock_model = MockXGBModel()
    with pytest.raises(ValueError, match="between 0 and 50"):
        run_traffic_reduction_scenario(sample_feature_row, reduction_pct=50.1, model=mock_model)

    with pytest.raises(ValueError, match="between 0 and 50"):
        run_traffic_reduction_scenario(sample_feature_row, reduction_pct=100, model=mock_model)


def test_negative_percentage_rejected(sample_feature_row):
    """Negative reduction must be strictly rejected with ValueError."""
    mock_model = MockXGBModel()
    with pytest.raises(ValueError, match="between 0 and 50"):
        run_traffic_reduction_scenario(sample_feature_row, reduction_pct=-5.0, model=mock_model)


def test_non_numeric_percentage_rejected(sample_feature_row):
    """Non-numeric reduction must be strictly rejected with TypeError."""
    mock_model = MockXGBModel()
    with pytest.raises(TypeError, match="must be numeric"):
        run_traffic_reduction_scenario(sample_feature_row, reduction_pct="twenty", model=mock_model)

    with pytest.raises(TypeError, match="must be numeric"):
        run_traffic_reduction_scenario(sample_feature_row, reduction_pct=True, model=mock_model)


def test_weather_and_pm25_lags_remain_unmodified(sample_feature_row):
    """Verifies weather, calendar, and PM2.5 lags are never altered in scenario features."""
    mock_model = MockXGBModel()
    res = run_traffic_reduction_scenario(sample_feature_row, reduction_pct=25, model=mock_model)

    # Features passed to model must have identical unmodified values
    for col in UNMODIFIED_FEATURES:
        assert col not in res["modified_features"]


def test_only_current_hour_traffic_features_modified(sample_feature_row):
    """Verifies that all 6 and only the 6 current-hour traffic-dependent features are modified."""
    mock_model = MockXGBModel()
    reduction_pct = 20.0
    factor = 0.8
    res = run_traffic_reduction_scenario(sample_feature_row, reduction_pct=reduction_pct, model=mock_model)

    mod_dict = res["modified_features"]
    assert set(mod_dict.keys()) == set(CURRENT_HOUR_TRAFFIC_FEATURES)

    for col in ["traffic_alankar", "traffic_jehangir", "traffic_rto", "traffic_total",
                "traffic_x_wind", "traffic_x_humidity"]:
        base_val = sample_feature_row[col]
        scen_val = mod_dict[col]["scenario"]
        assert scen_val == pytest.approx(base_val * factor, rel=1e-5)


def test_historical_traffic_rolling_means_remain_unmodified(sample_feature_row):
    """Verifies that historical rolling means (traffic_roll_mean_3h, traffic_roll_mean_6h) remain unchanged."""
    mock_model = MockXGBModel()
    res = run_traffic_reduction_scenario(sample_feature_row, reduction_pct=30.0, model=mock_model)

    assert "traffic_roll_mean_3h" not in res["modified_features"]
    assert "traffic_roll_mean_6h" not in res["modified_features"]


def test_traffic_total_is_exact_sum_of_reduced_zones(sample_feature_row):
    """Verifies that modified traffic_total equals the exact sum of modified zone counts."""
    mock_model = MockXGBModel()
    res = run_traffic_reduction_scenario(sample_feature_row, reduction_pct=25.0, model=mock_model)
    mod = res["modified_features"]
    sum_zones = (
        mod["traffic_alankar"]["scenario"]
        + mod["traffic_jehangir"]["scenario"]
        + mod["traffic_rto"]["scenario"]
    )
    assert mod["traffic_total"]["scenario"] == pytest.approx(sum_zones, rel=1e-5)


def test_model_feature_ordering_strictly_preserved(sample_feature_row):
    """Verifies that features are passed to the model in exact CITY_FEATURE_COLUMNS order."""
    mock_model = MockXGBModel()
    run_traffic_reduction_scenario(sample_feature_row, reduction_pct=30, model=mock_model)
    assert mock_model.last_features_seen == CITY_FEATURE_COLUMNS


def test_support_series_dataframe_dict_inputs(sample_feature_row):
    """Verifies function works identically with Series, DataFrame, and dict inputs."""
    mock_model = MockXGBModel()

    # Series input
    res_series = run_traffic_reduction_scenario(sample_feature_row, reduction_pct=25, model=mock_model)

    # DataFrame input
    df_row = pd.DataFrame([sample_feature_row.to_dict()])
    res_df = run_traffic_reduction_scenario(df_row, reduction_pct=25, model=mock_model)

    # Dict input
    dict_row = sample_feature_row.to_dict()
    res_dict = run_traffic_reduction_scenario(dict_row, reduction_pct=25, model=mock_model)

    assert res_series["scenario_prediction"] == res_df["scenario_prediction"]
    assert res_series["scenario_prediction"] == res_dict["scenario_prediction"]
    assert res_series["delta_pm25"] == res_df["delta_pm25"]
