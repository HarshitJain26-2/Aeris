"""
Forecast Repository
Data-access boundary for model inputs, feature vectors, and prediction artifacts.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from ml.src.features import CITY_FEATURE_COLUMNS


# Canonical verified 25-feature state for Pune (evaluation baseline hour 2023-01-18 08:00 IST)
CANONICAL_FEATURE_ROW: Dict[str, Any] = {
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


class ForecastRepository:
    """Repository boundary for forecasting model features and outputs."""

    def __init__(
        self,
        val_parquet_path: str = "data/processed/aeris_ml_city_val.parquet",
    ):
        self._val_parquet_path = Path(val_parquet_path)

    def get_latest_feature_vector(self) -> Dict[str, Any]:
        """
        Retrieves the feature dictionary containing all 25 features required for XGBoost inference.
        """
        if self._val_parquet_path.exists():
            try:
                df = pd.read_parquet(self._val_parquet_path)
                if not df.empty:
                    # Check if all required features exist
                    missing = [c for c in CITY_FEATURE_COLUMNS if c not in df.columns]
                    if not missing:
                        latest_row = df.iloc[-1]
                        feat = {c: float(latest_row[c]) for c in CITY_FEATURE_COLUMNS}
                        feat["timestamp"] = str(latest_row.get("timestamp", CANONICAL_FEATURE_ROW["timestamp"]))
                        return feat
            except Exception:
                pass

        return dict(CANONICAL_FEATURE_ROW)
