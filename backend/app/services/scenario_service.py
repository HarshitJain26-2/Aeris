"""
Scenario Service
Executes model-based counterfactual traffic reduction scenarios using the trained XGBoost model.
Reuses the existing scenario engine in ml/src/scenario.py.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import xgboost as xgb

from backend.app.repositories.forecast_repository import ForecastRepository
from backend.app.schemas.current import CpcbBand
from backend.app.schemas.scenario import (
    AirQualitySnapshot,
    ScenarioInputSnapshot,
    ScenarioResponse,
)
from backend.app.utils.cpcb_aqi import estimate_aqi_from_pm25, get_band_from_aqi
from ml.src.scenario import run_traffic_reduction_scenario
from ml.src.train import load_trained_model

logger = logging.getLogger("aeris.scenario_service")

DEFAULT_MODEL_PATH = "ml/models/xgb_pm25_forecaster.json"


class ScenarioService:
    """Service orchestrating counterfactual scenario simulations using ml/src/scenario.py."""

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        forecast_repo: Optional[ForecastRepository] = None,
    ):
        self._model_path = Path(model_path)
        self._forecast_repo = forecast_repo or ForecastRepository()
        self._model: Optional[xgb.XGBRegressor] = None

    def get_model(self) -> xgb.XGBRegressor:
        """Loads and caches the serialized XGBoost model artifact."""
        if self._model is not None:
            return self._model

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

        self._model = load_trained_model(str(target_path))
        logger.info(f"ScenarioService successfully loaded model from {target_path}")
        return self._model

    def simulate(
        self,
        traffic_reduction_pct: float,
        features: Optional[Dict[str, Any]] = None,
    ) -> ScenarioResponse:
        """
        Executes a real scenario simulation using the existing ml/src/scenario engine.

        At 0%: returns baseline model prediction with delta = 0.0.
        For 30%, 50%, etc.: executes genuine XGBoost inference under perturbed traffic predictors.
        """
        # Validate reduction percentage boundaries (0 <= value <= 50)
        if not isinstance(traffic_reduction_pct, (int, float)) or isinstance(traffic_reduction_pct, bool):
            raise TypeError(f"traffic_reduction_pct must be numeric, got {type(traffic_reduction_pct).__name__}")

        if traffic_reduction_pct < 0.0 or traffic_reduction_pct > 50.0:
            raise ValueError(
                f"traffic_reduction_pct must be between 0 and 50 inclusive, got {traffic_reduction_pct}"
            )

        model = self.get_model()

        # Retrieve feature vector (canonical evaluation hour or latest available)
        feat_dict = (
            features
            if features is not None
            else self._forecast_repo.get_verified_evaluation_feature_vector()
        )

        # Call the existing counterfactual scenario engine (ml/src/scenario.py strictly preserves 0-50%)
        result = run_traffic_reduction_scenario(
            features_row=feat_dict,
            reduction_pct=float(traffic_reduction_pct),
            model=model,
        )

        base_pm25 = float(result["baseline_prediction"])
        scen_pm25 = float(result["scenario_prediction"])
        delta_pm25 = float(result["delta_pm25"])
        pct_change = float(result["percent_change"])

        # Calculate CPCB AQI and band for both baseline and scenario
        base_aqi = estimate_aqi_from_pm25(base_pm25)
        base_band = get_band_from_aqi(base_aqi)

        scen_aqi = estimate_aqi_from_pm25(scen_pm25)
        scen_band = get_band_from_aqi(scen_aqi)

        delta_abs = round(abs(scen_pm25 - base_pm25), 4)
        delta_pct = round(abs(pct_change), 4)

        return ScenarioResponse(
            baseline_pm25=base_pm25,
            scenario_pm25=scen_pm25,
            delta=delta_pm25,
            traffic_reduction_pct=float(traffic_reduction_pct),
            dataSource="model_estimate",
            data_source="model_estimate",
            percent_change=pct_change,
            disclaimer=result["disclaimer"],
            modified_features=result.get("modified_features"),
            input=ScenarioInputSnapshot(trafficReductionPct=float(traffic_reduction_pct)),
            baseline=AirQualitySnapshot(
                pm25=base_pm25,
                aqi=base_aqi,
                aqiBand=CpcbBand(base_band),
            ),
            modelled=AirQualitySnapshot(
                pm25=scen_pm25,
                aqi=scen_aqi,
                aqiBand=CpcbBand(scen_band),
            ),
            deltaAbsolute=delta_abs,
            deltaPct=delta_pct,
            method="backend-solver",
            isModelEstimate=True,
        )


# Cached singleton instance for dependency injection
_scenario_service_instance: Optional[ScenarioService] = None


def get_scenario_service() -> ScenarioService:
    global _scenario_service_instance
    if _scenario_service_instance is None:
        _scenario_service_instance = ScenarioService()
    return _scenario_service_instance
