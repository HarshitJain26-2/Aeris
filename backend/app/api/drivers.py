"""
Driver Attribution API Router (backend/app/api/drivers.py)
----------------------------------------------------------
Exposes GET /api/v1/drivers providing model feature attribution from SHAP importance.
"""

from fastapi import APIRouter, Depends

from backend.app.schemas.drivers import DriverAttributionResponse
from backend.app.services.driver_service import DriverService

router = APIRouter(tags=["Driver Attribution"])

_driver_service_instance = None


def get_driver_service() -> DriverService:
    global _driver_service_instance
    if _driver_service_instance is None:
        _driver_service_instance = DriverService()
    return _driver_service_instance


@router.get(
    "/drivers",
    response_model=DriverAttributionResponse,
    summary="Get model-estimated feature attribution drivers",
    description=(
        "Returns normalized model feature attribution shares derived from mean absolute "
        "SHAP values computed across the validation holdout. These values quantify predictive "
        "feature importance and do not represent physical emission source apportionment."
    ),
)
def get_driver_attribution(
    service: DriverService = Depends(get_driver_service),
) -> DriverAttributionResponse:
    """Returns real model-driver feature attribution."""
    return service.compute_attribution()
