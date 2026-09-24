"""
Forecast Service
Executes genuine 1-hour-ahead PM2.5 forecasting using the trained XGBoost model artifact.
Strictly conforms to horizonHours=1, type='forecast', and dataSource='model_estimate'.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import xgboost as xgb

from backend.app.schemas.current import CpcbBand
from backend.app.schemas.forecast import ForecastPoint, ForecastResponse
from backend.app.repositories.forecast_repository import ForecastRepository
from backend.app.utils.cpcb_aqi import estimate_aqi_from_pm25, get_band_from_aqi
from ml.src.features import CITY_FEATURE_COLUMNS

logger = logging.getLogger("aeris.forecast_service")

DEFAULT_MODEL_PATH = "ml/models/xgb_pm25_forecaster.json"
DEFAULT_METRICS_PATH = "ml/evaluation/metrics.json"
MODEL_VERSION = "xgb-pm25-v1"


class ForecastService:
    """Service responsible for loading the trained XGBoost artifact and computing forecasts."""

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        metrics_path: str = DEFAULT_METRICS_PATH,
        forecast_repo: Optional[ForecastRepository] = None,
    ):
        self._model_path = Path(model_path)
        self._metrics_path = Path(metrics_path)
        self._forecast_repo = forecast_repo or ForecastRepository()
        self._model: Optional[xgb.XGBRegressor] = None
        self._rmse: float = 7.9029  # Default to evaluated validation RMSE

        # Initialize evaluation metrics if available
        self._load_metrics()

    def _load_metrics(self) -> None:
        """Loads evaluated RMSE for confidence interval calculation."""
        if self._metrics_path.exists():
            try:
                with open(self._metrics_path, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
                    self._rmse = float(metrics.get("rmse", 7.9029))
            except Exception as e:
                logger.warning(f"Could not read metrics from {self._metrics_path}: {e}")

    def get_model(self) -> xgb.XGBRegressor:
        """Loads and caches the serialized XGBoost model artifact."""
        if self._model is not None:
            return self._model

        # Check model file existence
        # Check relative to cwd or project root
        candidate_paths = [
            self._model_path,
            Path(__file__).resolve().parent.parent.parent.parent / self._model_path,
        ]
        target_path: Optional[Path] = None
        for p in candidate_paths:
            if p.exists():
                target_path = p
                break

        if target_path is None:
            raise FileNotFoundError(
                f"Trained XGBoost model artifact not found at {self._model_path}. "
                "Ensure ml/models/xgb_pm25_forecaster.json exists."
            )

        booster = xgb.Booster()
        booster.load_model(str(target_path))
        model = xgb.XGBRegressor()
        model._Booster = booster
        self._model = model
        logger.info(f"Successfully loaded XGBoost model from {target_path}")
        return self._model

    def generate_forecast(
        self,
        features: Optional[Dict[str, Any]] = None,
    ) -> ForecastResponse:
        """
        Generates a genuine 1-hour-ahead PM2.5 prediction for Pune.

        Constraints:
        - horizonHours = 1 (model is strictly 1-hour-ahead pm25_target_t_plus_1)
        - type = 'forecast'
        - dataSource = 'model_estimate'
        """
        model = self.get_model()

        # Retrieve feature vector
        feat_dict = features if features is not None else self._forecast_repo.get_latest_feature_vector()

        # Timestamp handling
        raw_ts = feat_dict.get("timestamp", "2023-01-18 08:00:00+05:30")
        try:
            feature_dt = pd.to_datetime(raw_ts)
            forecast_dt = feature_dt + pd.Timedelta(hours=1)
            forecast_ts_str = forecast_dt.isoformat()
        except Exception:
            forecast_ts_str = "2023-01-18T09:00:00+05:30"

        # Validate that all 25 features are present
        missing_features = [col for col in CITY_FEATURE_COLUMNS if col not in feat_dict]
        if missing_features:
            raise ValueError(f"Feature vector is missing required columns: {missing_features}")

        # Format input dataframe with exact feature ordering
        feature_df = pd.DataFrame([{col: float(feat_dict[col]) for col in CITY_FEATURE_COLUMNS}])[
            CITY_FEATURE_COLUMNS
        ]

        # Execute XGBoost inference
        preds = model.predict(feature_df)
        predicted_pm25 = round(float(preds[0]), 1)

        # Compute AQI and CPCB band
        aqi = estimate_aqi_from_pm25(predicted_pm25)
        aqi_band = get_band_from_aqi(aqi)

        # Compute 90% confidence interval (z ~ 1.645) using evaluated model RMSE
        margin = 1.645 * self._rmse
        pm25_lower = round(max(0.0, predicted_pm25 - margin), 1)
        pm25_upper = round(predicted_pm25 + margin, 1)

        forecast_point = ForecastPoint(
            timestamp=forecast_ts_str,
            pm25=predicted_pm25,
            aqi=aqi,
            aqiBand=CpcbBand(aqi_band),
            type="forecast",
            pm25Lower=pm25_lower,
            pm25Upper=pm25_upper,
            dataSource="model_estimate",
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        return ForecastResponse(
            city="Pune",
            generatedAt=now_iso,
            horizonHours=1,
            points=[forecast_point],
            modelVersion=MODEL_VERSION,
            dataSource="model_estimate",
        )
