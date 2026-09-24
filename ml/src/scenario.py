"""
AERIS Counterfactual Scenario Engine (ml/src/scenario.py)
=========================================================
Implements reproducible model-based what-if traffic intervention scenarios
for the AERIS Round 1 digital-twin vertical slice.

SCIENTIFIC DISCLOSURE & LIMITATIONS:
- This is a model-based counterfactual scenario using the trained XGBoost model.
- Labeled strictly as: "modeled traffic-reduction scenario" or "XGBoost counterfactual scenario".
- Does NOT represent physically observed data.
- Does NOT guarantee real-world causal outcomes.
- Target remains CAMS Global modeled atmospheric concentration; CAMS target is not modified.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd

from ml.src.features import CITY_FEATURE_COLUMNS
from ml.src.train import load_trained_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aeris.scenario")

# Features that directly depend on current-hour traffic counts (perturbed)
CURRENT_HOUR_TRAFFIC_FEATURES = [
    "traffic_alankar",
    "traffic_jehangir",
    "traffic_rto",
    "traffic_total",
    "traffic_x_wind",
    "traffic_x_humidity",
]

# Features that must remain completely unmodified (including historical traffic rolling context)
UNMODIFIED_FEATURES = [
    "traffic_roll_mean_3h",
    "traffic_roll_mean_6h",
    "temperature",
    "humidity",
    "wind_speed",
    "rainfall",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "pm25_lag_1h",
    "pm25_lag_2h",
    "pm25_lag_3h",
    "pm25_lag_6h",
    "pm25_lag_12h",
    "pm25_lag_24h",
    "pm25_roll_mean_3h",
    "pm25_roll_mean_6h",
    "pm25_roll_mean_12h",
    "pm25_roll_mean_24h",
]


def run_traffic_reduction_scenario(
    features_row: Union[pd.Series, pd.DataFrame, Dict[str, Any]],
    reduction_pct: Union[int, float],
    model: Optional[Any] = None,
    model_path: str = "ml/models/xgb_pm25_forecaster.json",
) -> Dict[str, Any]:
    """
    Executes a model-based counterfactual traffic reduction scenario (0-50%).

    Mechanics:
    1. Validates reduction_pct: must be numeric and between 0 and 50 inclusive.
    2. Takes a feature row at time t.
    3. Scales all traffic-dependent features by (1 - reduction_pct / 100.0).
    4. Preserves weather, PM2.5 autoregressive lags, and calendar features exactly.
    5. Evaluates the trained XGBoost model on both baseline and scenario feature vectors.
    6. Produces baseline prediction, scenario prediction, delta, and percentage change.

    Args:
        features_row: Hourly feature row at time t (Series, single-row DataFrame, or dict).
        reduction_pct: Percentage traffic reduction (0.0 to 50.0).
        model: Pre-loaded XGBoost model object (optional).
        model_path: Path to serialized XGBoost model JSON.

    Returns:
        Dict reporting baseline forecast, scenario forecast, delta_pm25,
        percent_change, and scientific counterfactual metadata.
    """
    # 1. Validate reduction_pct
    if not isinstance(reduction_pct, (int, float)) or isinstance(reduction_pct, bool):
        raise TypeError(f"reduction_pct must be numeric (int or float), got {type(reduction_pct).__name__}")

    if reduction_pct < 0.0 or reduction_pct > 50.0:
        raise ValueError(
            f"reduction_pct must be between 0 and 50 inclusive, got {reduction_pct}"
        )

    # 2. Parse feature row
    if isinstance(features_row, pd.DataFrame):
        if len(features_row) != 1:
            raise ValueError(f"features_row DataFrame must contain exactly 1 row, got {len(features_row)}")
        row_dict = features_row.iloc[0].to_dict()
    elif isinstance(features_row, pd.Series):
        row_dict = features_row.to_dict()
    elif isinstance(features_row, dict):
        row_dict = features_row.copy()
    else:
        raise TypeError(f"Unsupported features_row type: {type(features_row).__name__}")

    # Extract timestamp if present
    timestamp_str = str(row_dict.get("timestamp", "unknown"))

    # Verify all 25 features are present
    missing_cols = [c for c in CITY_FEATURE_COLUMNS if c not in row_dict]
    if missing_cols:
        raise KeyError(f"features_row missing required features: {missing_cols}")

    # 3. Build baseline feature vector
    base_features = {c: float(row_dict[c]) for c in CITY_FEATURE_COLUMNS}
    base_df = pd.DataFrame([base_features])[CITY_FEATURE_COLUMNS]

    # 4. Build scenario feature vector
    factor = 1.0 - (float(reduction_pct) / 100.0)
    scen_features = base_features.copy()

    # Scale direct current-hour traffic counts
    scen_features["traffic_alankar"] = base_features["traffic_alankar"] * factor
    scen_features["traffic_jehangir"] = base_features["traffic_jehangir"] * factor
    scen_features["traffic_rto"] = base_features["traffic_rto"] * factor
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

    # Verify unmodified features remained strictly untouched
    for col in UNMODIFIED_FEATURES:
        if scen_features[col] != base_features[col]:
            raise AssertionError(f"Unmodified feature '{col}' was altered during scenario generation.")

    scen_df = pd.DataFrame([scen_features])[CITY_FEATURE_COLUMNS]

    # 5. Load model and predict
    if model is None:
        model = load_trained_model(model_path)

    base_pred = float(model.predict(base_df)[0])
    scen_pred = float(model.predict(scen_df)[0])

    if not np.isfinite(base_pred) or not np.isfinite(scen_pred):
        raise ValueError(f"Non-finite prediction encountered: base={base_pred}, scen={scen_pred}")

    # Special-case 0% reduction identity
    if reduction_pct == 0.0:
        delta_pm25 = 0.0
        percent_change = 0.0
        scen_pred = base_pred
    else:
        delta_pm25 = scen_pred - base_pred
        percent_change = (delta_pm25 / base_pred * 100.0) if base_pred != 0.0 else 0.0

    return {
        "timestamp": timestamp_str,
        "reduction_pct": float(reduction_pct),
        "baseline_prediction": round(base_pred, 4),
        "scenario_prediction": round(scen_pred, 4),
        "delta_pm25": round(delta_pm25, 4),
        "percent_change": round(percent_change, 4),
        "model_source": "XGBoost (ml/models/xgb_pm25_forecaster.json)",
        "target_source": "CAMS Global Atmospheric Composition Forecasts",
        "scenario_type": "modeled traffic-reduction scenario",
        "counterfactual_label": "XGBoost counterfactual scenario",
        "disclaimer": (
            "The scenario engine perturbs current-hour traffic predictors only. Historical traffic "
            "context remains fixed. Because the forecasting model is predictive rather than causal, "
            "the learned counterfactual response may be non-monotonic and should not be interpreted "
            "as a guaranteed physical effect."
        ),
        "modified_features": {
            col: {
                "baseline": round(base_features[col], 4),
                "scenario": round(scen_features[col], 4),
                "factor": round(factor, 4),
            }
            for col in CURRENT_HOUR_TRAFFIC_FEATURES
        },
    }


def generate_scenario_artifacts(
    val_path: str = "data/processed/aeris_ml_city_val.parquet",
    model_path: str = "ml/models/xgb_pm25_forecaster.json",
    demo_output_path: str = "ml/evaluation/traffic_scenario_demo.json",
    sensitivity_output_path: str = "ml/evaluation/traffic_scenario_sensitivity.csv",
    representative_hour: str = "08:00",
    demo_reduction_pct: float = 25.0,
    sensitivity_percentages: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Generates scenario demonstration and sensitivity artifacts for evaluation.
    """
    if sensitivity_percentages is None:
        sensitivity_percentages = [5.0, 10.0, 25.0, 50.0]

    val_df = pd.read_parquet(val_path)
    matching_rows = val_df[val_df["timestamp"].astype(str).str.contains(representative_hour)]
    if matching_rows.empty:
        features_row = val_df.iloc[0]
        logger.warning(f"Hour {representative_hour} not found in validation; using first row.")
    else:
        features_row = matching_rows.iloc[0]

    model = load_trained_model(model_path)

    # 1. Generate Demo Artifact (e.g. 25% reduction)
    demo_result = run_traffic_reduction_scenario(
        features_row=features_row,
        reduction_pct=demo_reduction_pct,
        model=model,
    )

    p_demo = Path(demo_output_path)
    p_demo.parent.mkdir(parents=True, exist_ok=True)
    with open(p_demo, "w", encoding="utf-8") as f:
        json.dump(demo_result, f, indent=2)
    logger.info(f"Saved scenario demo artifact to {p_demo}")

    # 2. Generate Sensitivity Table (5%, 10%, 25%, 50%)
    sensitivity_rows = []
    for pct in sensitivity_percentages:
        res = run_traffic_reduction_scenario(
            features_row=features_row,
            reduction_pct=pct,
            model=model,
        )
        sensitivity_rows.append({
            "reduction_pct": pct,
            "baseline_prediction": res["baseline_prediction"],
            "scenario_prediction": res["scenario_prediction"],
            "delta_pm25": res["delta_pm25"],
            "percent_change": res["percent_change"],
        })

    sens_df = pd.DataFrame(sensitivity_rows)
    p_sens = Path(sensitivity_output_path)
    p_sens.parent.mkdir(parents=True, exist_ok=True)
    sens_df.to_csv(p_sens, index=False)
    logger.info(f"Saved scenario sensitivity table to {p_sens}")

    return {
        "demo": demo_result,
        "sensitivity": sensitivity_rows,
        "demo_path": str(p_demo),
        "sensitivity_path": str(p_sens),
    }


if __name__ == "__main__":
    artifacts = generate_scenario_artifacts()
    print("=== TRAFFIC REDUCTION SCENARIO DEMO ===")
    print(json.dumps(artifacts["demo"], indent=2))
    print("\n=== SENSITIVITY TABLE ===")
    print(pd.DataFrame(artifacts["sensitivity"]).to_string(index=False))
