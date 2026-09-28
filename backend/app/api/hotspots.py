"""
Hotspots API Router (backend/app/api/hotspots.py)
-------------------------------------------------
Exposes GET /api/v1/hotspots providing contextual/model-estimated urban hotspot points.

SCIENTIFIC PROVENANCE & TRANSPARENCY:
- Modeled atmospheric PM2.5 is derived from CAMS Global Atmospheric Composition Forecasts.
  It represents a uniform city-wide modeled concentration, NOT independent per-zone observed sensor data.
- Dominant driver is labeled 'Traffic' as the sole zone-varying model feature available in this construction.
  It is a contextual predictor label, NOT causal physical source apportionment.
- Data provenance is strictly 'model_estimate' (never 'observed' or 'DEMO_FIXTURE').
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.hotspots import HotspotGeoJSON
from backend.app.services.hotspot_service import HotspotService

router = APIRouter(tags=["Hotspots"])

_hotspot_service_instance = None


def get_hotspot_service() -> HotspotService:
    global _hotspot_service_instance
    if _hotspot_service_instance is None:
        _hotspot_service_instance = HotspotService()
    return _hotspot_service_instance


@router.get(
    "/hotspots",
    response_model=HotspotGeoJSON,
    summary="Get Pune urban environmental hotspots",
    description=(
        "Returns contextual/model-estimated hotspot feature points across the 3 documented "
        "Pune monitoring zones. PM2.5 is city-wide modeled concentration (CAMS Global atmospheric "
        "forecast) and is identical across zones. Hotspot intensity is normalized from zone-level "
        "traffic counts at the latest common timestamp. Dominant driver is contextual ('Traffic'). "
        "Data provenance is strictly 'model_estimate' (never ground-truth observed PM2.5 or causal source apportionment)."
    ),
)
def get_hotspots(
    service: HotspotService = Depends(get_hotspot_service),
) -> HotspotGeoJSON:
    """Returns real modeled environmental hotspots for Pune."""
    try:
        return service.get_hotspots()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Processed feature dataset is missing: {e}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No valid modeled PM2.5 data available: {e}",
        )
