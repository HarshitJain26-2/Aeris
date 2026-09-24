"""
AERIS Backend Application Entrypoint
FastAPI application exposing environmental intelligence, forecast, and zone APIs.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.current import router as current_router
from backend.app.api.forecast import router as forecast_router
from backend.app.api.zones import router as zones_router

app = FastAPI(
    title="AERIS API",
    description=(
        "Urban Environmental Intelligence & Digital Twin Backend for Pune.\n\n"
        "**Provenance Disclosure**: Round 1 PM2.5 target is based on CAMS Global Atmospheric Composition Forecasts "
        "(modeled atmospheric concentration). It is NOT CPCB observed ground-station data. "
        "The XGBoost forecaster provides a genuine 1-hour-ahead forecast (horizonHours = 1)."
    ),
    version="0.1.0",
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/", tags=["Health"])
def read_root():
    return {"message": "AERIS Backend is running"}


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


# Include API Routers under /api/v1
app.include_router(current_router, prefix="/api/v1", tags=["Air Quality"])
app.include_router(forecast_router, prefix="/api/v1", tags=["Forecast"])
app.include_router(zones_router, prefix="/api/v1", tags=["Zones"])
