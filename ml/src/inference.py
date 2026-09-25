"""
AERIS ML Inference Layer (ml/src/inference.py)
==============================================
Provides a clean, reusable inference layer for the AERIS digital-twin backend.

1-HOUR-AHEAD FORECASTING SEMANTICS:
- Input features represent conditions at timestamp t (input_timestamp).
- Prediction targets PM2.5 at timestamp t + 1 hour (forecast_timestamp).
- Target Source: CAMS Global Atmospheric Composition Forecasts (modeled atmospheric concentration).
- NOT Ground Truth: CAMS PM2.5 is modeled atmospheric data; it must NEVER be called ground truth
  or observed station data.
- Scenario Counterfactual: Model-based statistical simulation of traffic interventions (0–50%).
- NOT Observed Data: Counterfactual scenario outputs represent modeled responses and must NEVER
  be described as observed or physically guaranteed outcomes.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
import xgboost as xgb

from ml.src.features import CITY_FEATURE_COLUMNS

# Configure module logger
logger = logging.getLogger("aeris.inference")

# Default model path relative to project root
REPO_ROOT = root_dir
DEFAULT_MODEL_PATH = REPO_ROOT / "ml" / "models" / "xgb_pm25_forecaster.json"

# Traffic features modified during counterfactual intervention
CURRENT_HOUR_TRAFFIC_FEATURES = [
    "traffic_alankar",
    "traffic_jehangir",
    "traffic_rto",
    "traffic_total",
    "traffic_x_wind",
    "traffic_x_humidity",
]


class MissingFeatureError(ValueError, KeyError):
    """Raised when one or more required features are missing from the input."""
    pass


def _resolve_model_path(model_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolves model path, searching relative to CWD and repo root if necessary."""
    if model_path is None:
        target = DEFAULT_MODEL_PATH
    else:
        target = Path(model_path)

    if not target.exists():
        # Check relative to REPO_ROOT
        alt_path = REPO_ROOT / target
        if alt_path.exists():
            return alt_path
        raise FileNotFoundError(f"Model file not found at: {target}")

    return target


def load_forecaster(model_path: Optional[Union[str, Path]] = None) -> xgb.XGBRegressor:
    """
    Loads and returns the trained XGBoost PM2.5 forecasting model.

    Args:
        model_path: Path to serialized XGBoost model JSON. Defaults to
                    'ml/models/xgb_pm25_forecaster.json'.

    Returns:
        xgb.XGBRegressor with Booster loaded from file.
    """
    resolved_path = _resolve_model_path(model_path)
    booster = xgb.Booster()
    booster.load_model(str(resolved_path))
    model = xgb.XGBRegressor()
    model._Booster = booster
    logger.info(f"Loaded forecaster model successfully from {resolved_path}")
    return model


def compute_timestamps(raw_ts: Any) -> Tuple[str, str]:
    """
    Computes input_timestamp (t) and forecast_timestamp (t + 1 hour).
    Preserves timezone information if present.

    Returns:
        Tuple of (input_timestamp, forecast_timestamp) as ISO 8601 strings.
    """
    if raw_ts is None:
        return "unknown", "unknown"
    try:
        dt = pd.to_datetime(raw_ts)
        dt_plus_1 = dt + pd.Timedelta(hours=1)
        return dt.isoformat(), dt_plus_1.isoformat()
    except Exception:
        return str(raw_ts), "unknown"


def validate_features(
    features: Union[pd.Series, pd.DataFrame, Dict[str, Any]],
) -> Tuple[Dict[str, float], str, str]:
    """
    Validates feature input before model evaluation and resolves timestamp semantics.

    Validates:
    1. Input format: dict, pd.Series, or single-row pd.DataFrame.
    2. All 25 required model features exist.
    3. Correct feature ordering matches CITY_FEATURE_COLUMNS.
    4. Numeric features are finite (no NaN, Inf, None, bool, str).
    5. No unexpected missing required predictors.

    Args:
        features: Input feature vector as dict, Series, or 1-row DataFrame.

    Returns:
        Tuple of (clean_feature_dict, input_timestamp, forecast_timestamp).

    Raises:
        TypeError: If input features type is unsupported.
        ValueError / MissingFeatureError: If validation checks fail.
    """
    if not isinstance(features, (pd.DataFrame, pd.Series, dict)):
        raise TypeError(
            f"Unsupported features type: {type(features).__name__}. "
            "Expected dict, pd.Series, or pd.DataFrame."
        )

    if isinstance(features, pd.DataFrame):
        if len(features) != 1:
            raise ValueError(f"features DataFrame must contain exactly 1 row, got {len(features)} rows.")
        keys = list(features.columns)
        row_dict = features.iloc[0].to_dict()
    elif isinstance(features, pd.Series):
        keys = list(features.index)
        row_dict = features.to_dict()
    else:  # dict
        keys = list(features.keys())
        row_dict = features.copy()

    # Extract timestamps: features at t -> predict t + 1 hour
    raw_ts = (
        row_dict.get("input_timestamp")
        if row_dict.get("input_timestamp") is not None
        else (
            row_dict.get("timestamp")
            if row_dict.get("timestamp") is not None
            else row_dict.get("forecast_timestamp")
        )
    )
    input_timestamp, forecast_timestamp = compute_timestamps(raw_ts)

    # 1. Check for missing required features
    missing = [c for c in CITY_FEATURE_COLUMNS if c not in row_dict]
    if missing:
        raise MissingFeatureError(
            f"Input features missing {len(missing)} required predictor(s): {missing}"
        )

    # 2. Check for duplicate feature keys
    present_feature_keys = [k for k in keys if k in CITY_FEATURE_COLUMNS]
    if len(present_feature_keys) != len(set(present_feature_keys)):
        raise ValueError("Duplicate feature names detected in input.")

    # 3. Check correct feature ordering
    if present_feature_keys != CITY_FEATURE_COLUMNS:
        raise ValueError(
            f"Incorrect feature ordering. Expected features in canonical order: "
            f"{CITY_FEATURE_COLUMNS}. Received: {present_feature_keys}"
        )

    # 4. Check all 25 features are finite numbers
    clean_features: Dict[str, float] = {}
    for col in CITY_FEATURE_COLUMNS:
        val = row_dict[col]
        # In Python, bool is a subclass of int (isinstance(True, int) is True), so check bool explicitly
        if val is None or isinstance(val, (str, bool)):
            raise ValueError(
                f"Feature '{col}' must be a finite numeric value, got {type(val).__name__}: {val}"
            )
        try:
            val_f = float(val)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Feature '{col}' must be numeric, got {type(val).__name__}: {val}"
            ) from e

        if not np.isfinite(val_f):
            raise ValueError(
                f"Feature '{col}' contains non-finite value (NaN or Inf): {val}"
            )
        clean_features[col] = val_f

    return clean_features, input_timestamp, forecast_timestamp


def predict_next_hour(
    features: Union[pd.Series, pd.DataFrame, Dict[str, Any]],
    model: Optional[Any] = None,
    model_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Predicts 1-hour-ahead PM2.5 concentration using the trained XGBoost model.

    Target is modeled PM2.5 from CAMS Global Atmospheric Composition Forecasts.
    NOT ground truth or observed station measurements.

    Input features at timestamp t -> Forecast for timestamp t + 1 hour.

    Args:
        features: Feature vector matching the 25-feature schema.
        model: Optional pre-loaded XGBoost model. If None, loads from model_path.
        model_path: Optional path to serialized model JSON.

    Returns:
        Dict:
        {
            "input_timestamp": "...",
            "forecast_timestamp": "...",
            "pm25_forecast": float,
            "target_source": "CAMS Global Atmospheric Composition Forecasts",
            "target_source_type": "modeled"
        }
    """
    clean_features, input_timestamp, forecast_timestamp = validate_features(features)

    if model is None:
        model = load_forecaster(model_path)

    feature_df = pd.DataFrame([clean_features])[CITY_FEATURE_COLUMNS]
    pred = float(model.predict(feature_df)[0])

    if not np.isfinite(pred):
        raise ValueError(f"Model generated non-finite prediction: {pred}")

    return {
        "input_timestamp": input_timestamp,
        "forecast_timestamp": forecast_timestamp,
        "pm25_forecast": round(pred, 4),
        "target_source": "CAMS Global Atmospheric Composition Forecasts",
        "target_source_type": "modeled",
    }


def run_traffic_counterfactual(
    features: Union[pd.Series, pd.DataFrame, Dict[str, Any]],
    reduction_pct: Union[int, float],
    model: Optional[Any] = None,
    model_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Executes a model-based traffic reduction counterfactual scenario (0–50%).

    Input features at timestamp t -> Counterfactual forecast for timestamp t + 1 hour.

    SCIENTIFIC NOTE:
    - Modeled counterfactual scenario using statistical XGBoost forecaster.
    - Perturbs current-hour traffic predictors; historical traffic lags remain fixed.
    - NOT observed data and NOT a causal guarantee.

    Args:
        features: Feature vector matching the 25-feature schema.
        reduction_pct: Traffic reduction percentage (0 to 50 inclusive).
        model: Optional pre-loaded XGBoost model. If None, loads from model_path.
        model_path: Optional path to serialized model JSON.

    Returns:
        Dict:
        {
            "input_timestamp": "...",
            "forecast_timestamp": "...",
            "baseline_pm25": float,
            "scenario_pm25": float,
            "delta_pm25": float,
            "reduction_pct": float,
            "scenario_type": "modeled traffic-reduction scenario"
        }
    """
    # 1. Validate reduction_pct
    if not isinstance(reduction_pct, (int, float)) or isinstance(reduction_pct, bool):
        raise TypeError(
            f"reduction_pct must be numeric (int or float), got {type(reduction_pct).__name__}"
        )

    reduction_float = float(reduction_pct)
    if reduction_float < 0.0 or reduction_float > 50.0:
        raise ValueError(
            f"reduction_pct must be between 0 and 50 inclusive, got {reduction_pct}"
        )

    # 2. Validate input features
    clean_features, input_timestamp, forecast_timestamp = validate_features(features)

    # 3. Load model if not provided
    if model is None:
        model = load_forecaster(model_path)

    # 4. Predict baseline
    base_df = pd.DataFrame([clean_features])[CITY_FEATURE_COLUMNS]
    base_pred = float(model.predict(base_df)[0])

    # 5. Predict scenario
    if reduction_float == 0.0:
        # Identity condition: 0% reduction produces identical prediction
        scen_pred = base_pred
        delta_pm25 = 0.0
    else:
        factor = 1.0 - (reduction_float / 100.0)
        scen_features = clean_features.copy()

        # Perturb direct current-hour traffic
        scen_features["traffic_alankar"] = clean_features["traffic_alankar"] * factor
        scen_features["traffic_jehangir"] = clean_features["traffic_jehangir"] * factor
        scen_features["traffic_rto"] = clean_features["traffic_rto"] * factor
        scen_features["traffic_total"] = (
            scen_features["traffic_alankar"]
            + scen_features["traffic_jehangir"]
            + scen_features["traffic_rto"]
        )

        # Historical traffic rolling means (traffic_roll_mean_3h, traffic_roll_mean_6h)
        # remain strictly UNCHANGED because an intervention at hour t cannot rewrite past history.
        # Recompute physical interaction terms with modified current-hour traffic
        scen_features["traffic_x_wind"] = scen_features["traffic_total"] * scen_features["wind_speed"]
        scen_features["traffic_x_humidity"] = scen_features["traffic_total"] * scen_features["humidity"]

        scen_df = pd.DataFrame([scen_features])[CITY_FEATURE_COLUMNS]
        scen_pred = float(model.predict(scen_df)[0])
        delta_pm25 = scen_pred - base_pred

    if not np.isfinite(base_pred) or not np.isfinite(scen_pred):
        raise ValueError(
            f"Non-finite prediction encountered: base={base_pred}, scen={scen_pred}"
        )

    return {
        "input_timestamp": input_timestamp,
        "forecast_timestamp": forecast_timestamp,
        "baseline_pm25": round(base_pred, 4),
        "scenario_pm25": round(scen_pred, 4),
        "delta_pm25": round(delta_pm25, 4),
        "reduction_pct": reduction_float,
        "scenario_type": "modeled traffic-reduction scenario",
    }


if __name__ == "__main__":
    val_path = REPO_ROOT / "data" / "processed" / "aeris_ml_city_val.parquet"
    if val_path.exists():
        val_df = pd.read_parquet(val_path)
        sample_row = val_df.iloc[8]  # 08:00 AM rush hour
        print("=== Real Validation Row Inference Demo (Hour 08:00 IST -> Forecast 09:00 IST) ===")
        forecast_res = predict_next_hour(sample_row)
        print(json.dumps(forecast_res, indent=2))

        print("\n=== Real Validation Row 25% Traffic Counterfactual Demo ===")
        counterfactual_res = run_traffic_counterfactual(sample_row, 25.0)
        print(json.dumps(counterfactual_res, indent=2))
    else:
        print(f"Validation dataset not found at {val_path}")
