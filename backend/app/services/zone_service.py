"""
Zone Service
Encapsulates business logic for monitored urban zones.
"""
from typing import List, Optional
from backend.app.schemas.zones import Zone
from backend.app.repositories.zone_repository import ZoneRepository


class ZoneService:
    """Service providing access to monitored urban zones."""

    def __init__(self, zone_repo: Optional[ZoneRepository] = None):
        self._zone_repo = zone_repo or ZoneRepository()

    def get_zones(self) -> List[Zone]:
        """Returns the list of monitored junction zones in Pune."""
        return self._zone_repo.list_zones()

    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Returns details for a specific junction zone."""
        return self._zone_repo.get_by_id(zone_id)
