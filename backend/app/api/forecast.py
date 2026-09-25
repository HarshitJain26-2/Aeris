"""
AERIS Forecast API Router (backend/app/api/forecast.py)
=======================================================
Exposes POST /api/v1/forecast for 1-hour-ahead PM2.5 city forecasting.

SCIENTIFIC SEMANTICS:
- input_timestamp: timestamp t of supplied predictors.
- forecast_timestamp: timestamp t + 1 hour of modeled CAMS PM2.5 forecast.
- target_source: "CAMS Global Atmospheric Composition Forecasts"
- target_source_type: "modeled"
"""

from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.app.services.inference_service import run_forecast_service

router = APIRouter(prefix="/api/v1", tags=["forecast"])


class ForecastRequest(BaseModel):
    """
    Validated request schema containing all 25 canonical ML predictors
    and the predictor observation timestamp t.
    """
    temperature: float
    humidity: float
    wind_speed: float
    rainfall: float
    traffic_alankar: float
    traffic_jehangir: float
    traffic_rto: float
    traffic_total: float
    hour_of_day: int
    day_of_week: int
    is_weekend: int
    pm25_lag_1h: float
    pm25_lag_2h: float
    pm25_lag_3h: float
    pm25_lag_6h: float
    pm25_lag_12h: float
    pm25_lag_24h: float
    pm25_roll_mean_3h: float
    pm25_roll_mean_6h: float
    pm25_roll_mean_12h: float
    pm25_roll_mean_24h: float
    traffic_roll_mean_3h: float
    traffic_roll_mean_6h: float
    traffic_x_wind: float
    traffic_x_humidity: float
    input_timestamp: datetime


class ForecastResponse(BaseModel):
    """
    Stable response schema reporting 1-hour-ahead PM2.5 forecast and scientific metadata.
    """
    input_timestamp: str
    forecast_timestamp: str
    pm25_forecast: float
    target_source: str
    target_source_type: str


@router.post("/forecast", response_model=ForecastResponse)
def create_forecast(request: ForecastRequest) -> ForecastResponse:
    """
    Computes 1-hour-ahead PM2.5 forecast from verified urban predictors.

    Returns:
        ForecastResponse:
        {
            "input_timestamp": "...",
            "forecast_timestamp": "...",
            "pm25_forecast": ...,
            "target_source": "CAMS Global Atmospheric Composition Forecasts",
            "target_source_type": "modeled"
        }
    """
    try:
        result = run_forecast_service(request)
        return ForecastResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
