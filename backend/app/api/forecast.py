"""
Forecast API Router
Exposes GET /api/v1/forecast
"""
from fastapi import APIRouter, Depends
from backend.app.schemas.forecast import ForecastResponse
from backend.app.services.forecast_service import ForecastService

router = APIRouter()

# Singleton or cached forecast service instance
_forecast_service_instance = None


def get_forecast_service() -> ForecastService:
    global _forecast_service_instance
    if _forecast_service_instance is None:
        _forecast_service_instance = ForecastService()
    return _forecast_service_instance


@router.get(
    "/forecast",
    response_model=ForecastResponse,
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
) -> ForecastResponse:
    """Returns genuine 1-hour-ahead PM2.5 forecast."""
    return service.generate_forecast()
