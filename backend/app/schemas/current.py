"""
Current Air Quality Schemas
Matches frontend/src/types/airQuality.ts
"""
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class CpcbBand(str, Enum):
    GOOD = "Good"
    SATISFACTORY = "Satisfactory"
    MODERATE = "Moderate"
    POOR = "Poor"
    VERY_POOR = "Very Poor"
    SEVERE = "Severe"


class AirQualityReading(BaseModel):
    timestamp: str = Field(..., description="ISO 8601 timestamp of the reading")
    city: str = Field(..., description="City or location name (e.g. Pune)")
    station: str = Field(..., description="Station or area name")
    pm25: float = Field(..., description="PM2.5 concentration in µg/m³")
    pm10: float = Field(..., description="PM10 concentration in µg/m³")
    aqi: int = Field(..., description="India National AQI (CPCB)")
    aqiBand: CpcbBand = Field(..., description="CPCB AQI band")
    temperatureC: float = Field(..., description="Temperature in °C")
    humidityPct: float = Field(..., description="Relative humidity %")
    trafficIndex: float = Field(..., description="Normalised traffic congestion index 0–100")
    windSpeedKmh: float = Field(..., description="Wind speed in km/h")
    dataSource: Literal["observed", "model_estimate", "DEMO_FIXTURE"] = Field(
        ...,
        description=(
            "Data provenance. Strictly 'model_estimate' when reporting CAMS Global modeled PM2.5."
        ),
    )
