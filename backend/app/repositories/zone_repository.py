"""
Zone Repository
Data-access boundary for documented urban monitoring zones.
Strictly restricted to the 3 documented ML zones.
"""
from typing import Dict, List, Optional
from backend.app.schemas.zones import Zone


DOCUMENTED_ZONES: List[Zone] = [
    Zone(
        zone_id="PUNE_ALANKAR_CHOWK",
        name="Alankar Chowk",
        latitude=18.5284,
        longitude=73.8741,
        description="Alankar Chowk / Ambedkar Rd intersection",
    ),
    Zone(
        zone_id="PUNE_JEHANGIR_CHOWK",
        name="Jehangir Chowk",
        latitude=18.5310,
        longitude=73.8775,
        description="Jehangir Hospital / Sasoon Rd intersection",
    ),
    Zone(
        zone_id="PUNE_RTO_CHOWK",
        name="RTO Chowk",
        latitude=18.5314,
        longitude=73.8648,
        description="Regional Transport Office (RTO) Chowk / Sangam Bridge",
    ),
]


class ZoneRepository:
    """Repository for urban junction zones."""

    def __init__(self, zones: Optional[List[Zone]] = None):
        self._zones: List[Zone] = zones if zones is not None else list(DOCUMENTED_ZONES)
        self._by_id: Dict[str, Zone] = {z.zone_id: z for z in self._zones}

    def list_zones(self) -> List[Zone]:
        """Returns the list of monitored zones."""
        return list(self._zones)

    def get_by_id(self, zone_id: str) -> Optional[Zone]:
        """Fetches a specific zone by ID."""
        return self._by_id.get(zone_id)
