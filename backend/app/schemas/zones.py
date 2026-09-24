"""
Zone Schemas
Defines documented ML monitoring zones.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class Zone(BaseModel):
    zone_id: str = Field(..., description="Canonical zone identifier, e.g. PUNE_ALANKAR_CHOWK")
    name: str = Field(..., description="Human-readable name of the junction")
    latitude: float = Field(..., description="Latitude coordinate (WGS84)")
    longitude: float = Field(..., description="Longitude coordinate (WGS84)")
    description: Optional[str] = Field(None, description="Detailed junction/corridor description")


class ZoneListResponse(BaseModel):
    city: str = Field("Pune", description="City name")
    zones: List[Zone] = Field(..., description="List of monitored urban zones")
