"""
AERIS Pydantic Schemas
"""
from backend.app.schemas.current import AirQualityReading, CpcbBand
from backend.app.schemas.drivers import (
    DriverAttribution,
    DriverAttributionResponse,
    DriverCategory,
)
from backend.app.schemas.forecast import ForecastPoint, ForecastResponse
from backend.app.schemas.hotspots import (
    HotspotFeature,
    HotspotGeoJSON,
    HotspotMetadata,
    HotspotPointGeometry,
    HotspotProperties,
)
from backend.app.schemas.scenario import (
    AirQualitySnapshot,
    ScenarioInputSnapshot,
    ScenarioRequest,
    ScenarioResponse,
)
from backend.app.schemas.zones import Zone, ZoneListResponse

__all__ = [
    "AirQualityReading",
    "AirQualitySnapshot",
    "CpcbBand",
    "DriverAttribution",
    "DriverAttributionResponse",
    "DriverCategory",
    "ForecastPoint",
    "ForecastResponse",
    "HotspotFeature",
    "HotspotGeoJSON",
    "HotspotMetadata",
    "HotspotPointGeometry",
    "HotspotProperties",
    "ScenarioInputSnapshot",
    "ScenarioRequest",
    "ScenarioResponse",
    "Zone",
    "ZoneListResponse",
]
