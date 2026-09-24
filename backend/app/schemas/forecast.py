"""
Forecast API Schemas
Matches frontend/src/types/forecast.ts
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.current import CpcbBand


class ForecastPoint(BaseModel):
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    pm25: float = Field(..., description="PM2.5 concentration in µg/m³")
    aqi: int = Field(..., description="India National AQI (CPCB)")
    aqiBand: CpcbBand = Field(..., description="CPCB AQI band")
    type: Literal["observed", "forecast"] = Field(
        ..., description="'observed' = actual sensor reading; 'forecast' = model prediction"
    )
    pm25Lower: Optional[float] = Field(
        None, description="Lower bound of 90% confidence interval (forecast only)"
    )
    pm25Upper: Optional[float] = Field(
        None, description="Upper bound of 90% confidence interval (forecast only)"
    )
    dataSource: Literal["observed", "model_estimate", "DEMO_FIXTURE"] = Field(
        ..., description="Data provenance — strictly 'model_estimate' for XGBoost forecasts"
    )


class ForecastResponse(BaseModel):
    city: str = Field(..., description="Target city (e.g. Pune)")
    generatedAt: str = Field(..., description="ISO 8601 timestamp of forecast generation")
    horizonHours: int = Field(
        ...,
        description="Forecast horizon in hours (strictly 1 for 1-hour-ahead model)",
    )
    points: List[ForecastPoint] = Field(..., description="List of forecast points")
    modelVersion: str = Field(
        ...,
        description="Stable model version identifier (e.g. xgb-pm25-v1)",
    )
    dataSource: Literal["model_estimate", "DEMO_FIXTURE"] = Field(
        ..., description="Provenance of the overall forecast response"
    )
