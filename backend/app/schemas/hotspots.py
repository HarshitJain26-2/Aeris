"""
Hotspot Schemas (backend/app/schemas/hotspots.py)
------------------------------------------------
Defines GeoJSON schemas for urban environmental hotspots in Pune.
Conforms strictly to the frontend HotspotGeoJSON contract in frontend/src/types/hotspot.ts.

SCIENTIFIC PROVENANCE & SEMANTICS:
- Atmospheric PM2.5 target is derived from CAMS Global Atmospheric Composition Forecasts.
- It is city-wide modeled atmospheric PM2.5, NOT independent per-zone observed sensor data.
- Dominant driver is labeled 'Traffic' based on available spatial traffic covariates.
  This is a contextual model-feature attribution label and NOT causal source apportionment.
  Industrial and Residential/Biomass fractions are not fabricated.
- Data provenance is strictly 'model_estimate' (never 'observed' or 'DEMO_FIXTURE').
"""

from typing import List, Literal
from pydantic import BaseModel, Field

from backend.app.schemas.current import CpcbBand


class HotspotPointGeometry(BaseModel):
    """GeoJSON Point geometry with [longitude, latitude] coordinates."""

    type: Literal["Point"] = "Point"
    coordinates: List[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="GeoJSON Point coordinates in WGS84: [longitude, latitude]",
    )


class HotspotProperties(BaseModel):
    """
    Properties for a single urban environmental hotspot feature.
    Matches frontend/src/types/hotspot.ts HotspotProperties.
    """

    id: str = Field(..., description="Unique zone identifier (e.g. PUNE_ALANKAR_CHOWK)")
    name: str = Field(..., description="Display name of the zone (e.g. Alankar Chowk)")
    locality: str = Field(..., description="Locality or intersection name")
    pm25: float = Field(
        ...,
        description="City-wide CAMS modeled PM2.5 atmospheric concentration in µg/m³",
    )
    aqi: int = Field(..., ge=0, le=500, description="India National AQI (CPCB)")
    aqiBand: CpcbBand = Field(..., description="CPCB AQI band")
    dominantDriver: Literal["Traffic", "Industrial", "Residential/Biomass"] = Field(
        "Traffic",
        description=(
            "Contextual model feature label ('Traffic'). "
            "NOTE: This is NOT physical emission-source apportionment or causal proof."
        ),
    )
    intensity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized spatial hotspot intensity based on zone traffic count, clamped to [0, 1]",
    )
    dataSource: Literal["observed", "model_estimate", "DEMO_FIXTURE"] = Field(
        "model_estimate",
        description="Data provenance. Strictly 'model_estimate'.",
    )


class HotspotFeature(BaseModel):
    """GeoJSON Feature representing a single monitoring zone hotspot."""

    type: Literal["Feature"] = "Feature"
    geometry: HotspotPointGeometry
    properties: HotspotProperties


class HotspotMetadata(BaseModel):
    """Metadata describing the hotspot FeatureCollection."""

    city: str = Field("Pune", description="City name")
    generatedAt: str = Field(
        ...,
        description="ISO 8601 timezone-aware timestamp of the modeled hotspot data represented by the response",
    )
    dataSource: Literal["observed", "model_estimate", "DEMO_FIXTURE"] = Field(
        "model_estimate",
        description="Dataset provenance. Strictly 'model_estimate'.",
    )


class HotspotGeoJSON(BaseModel):
    """
    GeoJSON FeatureCollection representing urban environmental hotspots in Pune.
    Matches frontend/src/types/hotspot.ts HotspotGeoJSON.
    """

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[HotspotFeature] = Field(..., description="List of hotspot features")
    metadata: HotspotMetadata = Field(..., description="Hotspot generation metadata")
