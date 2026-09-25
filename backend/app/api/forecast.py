"""
Forecast API Router (backend/app/api/forecast.py)
--------------------------------------------------
Exposes endpoints for PM2.5 city forecasting:
- GET  /api/v1/forecast: Dashboard forecast summary (1-hour-ahead estimate).
- POST /api/v1/forecast: Dynamic 1-hour-ahead ML inference from 25 canonical predictors.

SCIENTIFIC SEMANTICS:
- input_timestamp: timestamp t of supplied predictors.
- forecast_timestamp: timestamp t + 1 hour of modeled CAMS PM2.5 forecast.
- target_source: "CAMS Global Atmospheric Composition Forecasts"
- target_source_type: "modeled"
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.app.schemas.forecast import ForecastResponse as DashboardForecastResponse
from backend.app.services.forecast_service import ForecastService
from backend.app.services.inference_service import run_forecast_service

router = APIRouter(tags=["Forecast"])

# Singleton or cached forecast service instance
_forecast_service_instance = None


def get_forecast_service() -> ForecastService:
    global _forecast_service_instance
    if _forecast_service_instance is None:
        _forecast_service_instance = ForecastService()
    return _forecast_service_instance


@router.get(
    "/forecast",
    response_model=DashboardForecastResponse,
    summary="Get 1-hour-ahead PM2.5 forecast",
    description=(
        "Generates a genuine 1-hour-ahead PM2.5 prediction for Pune using the serialized XGBoost "
        "model artifact (xgb-pm25-v1). The model predicts pm25_target_t_plus_1 = PM2.5(t+1) based "
        "on the CAMS Global modeled atmospheric target. Horizon is strictly 1 hour (horizonHours = 1) "
        "with provenance strictly labeled as 'model_estimate'."
    ),
)
def get_pm25_forecast(
    service: ForecastService = Depends(get_forecast_service),
) -> DashboardForecastResponse:
    """Returns genuine 1-hour-ahead PM2.5 forecast."""
    return service.generate_forecast()


class ForecastRequest(BaseModel):
    """
    Validated request schema containing all 25 canonical ML predictors
    and the predictor observation timestamp t.
    """
    temperature: float
    humidity: float
    wind_speed: float
    rainfall: float
    traffic_alankar: float
    traffic_jehangir: float
    traffic_rto: float
    traffic_total: float
    hour_of_day: int
    day_of_week: int
    is_weekend: int
    pm25_lag_1h: float
    pm25_lag_2h: float
    pm25_lag_3h: float
    pm25_lag_6h: float
    pm25_lag_12h: float
    pm25_lag_24h: float
    pm25_roll_mean_3h: float
    pm25_roll_mean_6h: float
    pm25_roll_mean_12h: float
    pm25_roll_mean_24h: float
    traffic_roll_mean_3h: float
    traffic_roll_mean_6h: float
    traffic_x_wind: float
    traffic_x_humidity: float
    input_timestamp: datetime


class InferenceForecastResponse(BaseModel):
    """
    Stable response schema reporting 1-hour-ahead PM2.5 forecast and scientific metadata.
    """
    input_timestamp: str
    forecast_timestamp: str
    pm25_forecast: float
    target_source: str
    target_source_type: str


@router.post(
    "/forecast",
    response_model=InferenceForecastResponse,
)
def create_forecast(request: ForecastRequest) -> InferenceForecastResponse:
    """
    Computes 1-hour-ahead PM2.5 forecast from verified urban predictors.

    Returns:
        InferenceForecastResponse:
        {
            "input_timestamp": "...",
            "forecast_timestamp": "...",
            "pm25_forecast": ...,
            "target_source": "CAMS Global Atmospheric Composition Forecasts",
            "target_source_type": "modeled"
        }
    """
    try:
        result = run_forecast_service(request)
        return InferenceForecastResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
