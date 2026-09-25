"""
AERIS ML Inference Demo Script (ml/src/inference_demo.py)
==========================================================
Demonstrates the inference layer using a real historical validation row from
data/processed/aeris_ml_city_val.parquet.

1-HOUR-AHEAD FORECASTING SEMANTICS:
- input_timestamp:    time t of observed predictors
- forecast_timestamp: time t + 1 hour of modeled CAMS target

SCIENTIFIC DISCLOSURE:
- The PM2.5 forecast targets CAMS Global modeled atmospheric concentration, NOT ground truth.
- Traffic counterfactuals are statistical simulations from the trained XGBoost model,
  NOT observed measurements or guaranteed physical outcomes.
"""

import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd

from ml.src.inference import (
    load_forecaster,
    predict_next_hour,
    run_traffic_counterfactual,
)


def run_demo() -> None:
    val_path = root_dir / "data" / "processed" / "aeris_ml_city_val.parquet"
    if not val_path.exists():
        raise FileNotFoundError(f"Validation dataset not found: {val_path}")

    val_df = pd.read_parquet(val_path)
    # Use real validation row 8 (08:00 AM morning peak hour)
    real_row = val_df.iloc[8]

    print("=================================================================")
    print("           AERIS ML INFERENCE LAYER DEMONSTRATION                ")
    print("=================================================================")
    print(f"Validation Dataset Source:       {val_path}")
    print(f"Supplied Input Timestamp (t):    {real_row['timestamp']}")
    print(f"Target Forecast Timestamp (t+1): 2023-01-18 09:00:00+05:30")
    print(f"Reported CAMS PM2.5 (t+1):       {real_row['pm25_target_t_plus_1']} ug/m3")
    print("-----------------------------------------------------------------")

    # 1. Load Forecaster
    print("\n1. Loading forecaster...")
    model = load_forecaster()
    print("   Model loaded successfully.")

    # 2. Predict Next Hour
    print("\n2. Running 1-hour-ahead forecast predict_next_hour()...")
    forecast_output = predict_next_hour(real_row, model=model)
    print("   Output dictionary:")
    print(json.dumps(forecast_output, indent=4))

    # 3. Run Traffic Counterfactual (25% reduction)
    print("\n3. Running 25% traffic counterfactual run_traffic_counterfactual()...")
    counterfactual_output = run_traffic_counterfactual(real_row, reduction_pct=25.0, model=model)
    print("   Output dictionary:")
    print(json.dumps(counterfactual_output, indent=4))

    print("\n=================================================================")
    print("Demo completed successfully using real validation row.")


if __name__ == "__main__":
    run_demo()
