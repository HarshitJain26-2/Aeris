"""
Scenario API Schemas
Matches both backend specification and frontend scenario contract.
"""
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.current import CpcbBand


class AirQualitySnapshot(BaseModel):
    """Snapshot of PM2.5, AQI, and CPCB band for baseline or scenario."""
    pm25: float = Field(..., description="PM2.5 concentration in µg/m³")
    aqi: int = Field(..., description="India National AQI (CPCB)")
    aqiBand: CpcbBand = Field(..., description="CPCB AQI band classification")


class ScenarioInputSnapshot(BaseModel):
    """Input snapshot matching frontend scenario interface."""
    trafficReductionPct: float = Field(..., description="Traffic reduction percentage (0 to 50)")


class ScenarioRequest(BaseModel):
    """
    Request schema for POST /api/scenario/simulate.
    Validates traffic reduction percentage strictly: 0 <= value <= 50.
    Rejects negative values, values > 50, and non-numeric values.
    """
    traffic_reduction_pct: float = Field(
        ...,
        ge=0.0,
        le=50.0,
        alias="trafficReductionPct",
        description="Percentage reduction in traffic volume (0 to 50%).",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "traffic_reduction_pct": 30.0
            }
        },
    )


class ScenarioResponse(BaseModel):
    """
    Response schema for POST /api/scenario/simulate.
    Conforms to both AERIS backend specification and frontend scenario contract.
    All predictions are labeled with model_estimate provenance.
    """
    baseline_pm25: float = Field(
        ...,
        description="Model-estimated baseline PM2.5 forecast without intervention (µg/m³).",
    )
    scenario_pm25: float = Field(
        ...,
        description="Model-estimated scenario PM2.5 forecast under specified traffic reduction (µg/m³).",
    )
    delta: float = Field(
        ...,
        description="Scenario delta: scenario_pm25 - baseline_pm25 (µg/m³).",
    )
    traffic_reduction_pct: float = Field(
        ...,
        description="Evaluated traffic reduction percentage (0 to 50%).",
    )
    dataSource: Literal["model_estimate"] = Field(
        default="model_estimate",
        description="Data provenance — strictly 'model_estimate' (never observed ground truth).",
    )
    data_source: Literal["model_estimate"] = Field(
        default="model_estimate",
        description="Alias for data provenance in snake_case.",
    )
    percent_change: float = Field(
        ...,
        description="Model-estimated percentage change: (delta / baseline_pm25) * 100 (%).",
    )
    disclaimer: str = Field(
        ...,
        description=(
            "Scientific limitation disclosure: The scenario engine perturbs current-hour traffic "
            "predictors only. Historical traffic context remains fixed. Because the forecasting model "
            "is predictive rather than causal, the learned counterfactual response may be non-monotonic "
            "and represents a model estimate rather than a guaranteed physical outcome."
        ),
    )
    modified_features: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Breakdown of perturbed traffic-dependent features (baseline vs scenario).",
    )

    # Frontend-compatible contract fields (matches frontend/src/types/scenario.ts ScenarioResult)
    input: Optional[ScenarioInputSnapshot] = Field(
        default=None,
        description="Frontend-compatible input snapshot",
    )
    baseline: Optional[AirQualitySnapshot] = Field(
        default=None,
        description="Frontend-compatible baseline snapshot",
    )
    modelled: Optional[AirQualitySnapshot] = Field(
        default=None,
        description="Frontend-compatible modelled scenario snapshot",
    )
    deltaAbsolute: Optional[float] = Field(
        default=None,
        description="Absolute difference in PM2.5 between baseline and scenario",
    )
    deltaPct: Optional[float] = Field(
        default=None,
        description="Absolute percentage difference in PM2.5",
    )
    method: Literal["backend-solver"] = Field(
        default="backend-solver",
        description="Simulation method identifier",
    )
    isModelEstimate: Literal[True] = Field(
        default=True,
        description="Strictly true for all model-estimated scenario outputs",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "baseline_pm25": 68.0,
                "scenario_pm25": 61.2,
                "delta": -6.8,
                "traffic_reduction_pct": 30.0,
                "dataSource": "model_estimate",
                "percent_change": -10.0,
                "disclaimer": "Model-estimated scenario change under the specified traffic reduction.",
            }
        },
    )
