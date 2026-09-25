"""
Current Air Quality API Router
Exposes GET /api/v1/current
"""
from fastapi import APIRouter, Depends
from backend.app.schemas.current import AirQualityReading
from backend.app.services.current_service import CurrentAirQualityService

router = APIRouter()


def get_current_service() -> CurrentAirQualityService:
    return CurrentAirQualityService()


@router.get(
    "/current",
    response_model=AirQualityReading,
    summary="Get current Pune air quality reading",
    description=(
        "Returns the latest verified air quality readings for Pune. "
        "PROVENANCE DISCLOSURE: When reporting atmospheric PM2.5 based on CAMS Global forecasts, "
        "the provenance is strictly modeled ('model_estimate'). It is NOT ground-truth "
        "Pune ground-station PM2.5 or CPCB observed sensor data."
    ),
)
def get_current_air_quality(
    service: CurrentAirQualityService = Depends(get_current_service),
) -> AirQualityReading:
    """Returns current air quality condition for Pune."""
    return service.get_current_reading()
