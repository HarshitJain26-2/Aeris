"""
Zones API Router
Exposes GET /api/v1/zones
"""
from typing import List
from fastapi import APIRouter, Depends
from backend.app.schemas.zones import Zone
from backend.app.services.zone_service import ZoneService

router = APIRouter()


def get_zone_service() -> ZoneService:
    return ZoneService()


@router.get(
    "/zones",
    response_model=List[Zone],
    summary="Get monitored urban zones",
    description=(
        "Returns the 3 documented ML junction zones in Pune: "
        "PUNE_ALANKAR_CHOWK, PUNE_JEHANGIR_CHOWK, and PUNE_RTO_CHOWK."
    ),
)
def get_monitored_zones(
    service: ZoneService = Depends(get_zone_service),
) -> List[Zone]:
    """Returns list of monitored junction zones."""
    return service.get_zones()
