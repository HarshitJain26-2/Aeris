"""
AERIS API Routers
"""
from backend.app.api.current import router as current_router
from backend.app.api.forecast import router as forecast_router
from backend.app.api.zones import router as zones_router

__all__ = [
    "current_router",
    "forecast_router",
    "zones_router",
]
