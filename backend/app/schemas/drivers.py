"""
Driver Attribution Schemas (backend/app/schemas/drivers.py)
----------------------------------------------------------
Matches frontend/src/types/source.ts:
- DriverCategory
- DriverAttribution
- DriverAttributionResponse

SCIENTIFIC SEMANTICS:
Percentages represent normalized mean absolute SHAP feature-attribution shares.
They describe model predictive feature sensitivity, NOT physical emission-source
apportionment, and must never be interpreted as causal proof of PM2.5 generation.
"""

from typing import List, Literal
from pydantic import BaseModel, Field

DriverCategory = Literal[
    "Recent PM2.5 history",
    "Weather",
    "Traffic",
    "Time / calendar",
]


class DriverAttribution(BaseModel):
    category: DriverCategory = Field(
        ...,
        description="Model feature driver category",
    )
    estimatedPct: float = Field(
        ...,
        description="Normalized mean absolute SHAP feature-attribution share (%)",
    )
    ciLower: float = Field(
        ...,
        description=(
            "Contract field preserved for frontend compatibility; identical to estimatedPct "
            "as SHAP summary artifact does not provide parametric confidence intervals."
        ),
    )
    ciUpper: float = Field(
        ...,
        description=(
            "Contract field preserved for frontend compatibility; identical to estimatedPct "
            "as SHAP summary artifact does not provide parametric confidence intervals."
        ),
    )
    description: str = Field(
        ...,
        description="Human-readable description of feature attribution semantics",
    )


class DriverAttributionResponse(BaseModel):
    city: str = Field(..., description="Target city (e.g. Pune)")
    period: str = Field(..., description="Validation holdout / feature attribution context")
    drivers: List[DriverAttribution] = Field(
        ...,
        description="List of 4 canonical model feature attribution groups",
    )
    method: Literal["model_feature_attribution", "DEMO_FIXTURE"] = Field(
        ...,
        description="Attribution method — strictly 'model_feature_attribution'",
    )
    disclaimer: str = Field(
        ...,
        description="Scientific disclaimer clarifying non-causal SHAP feature attribution",
    )
    dataSource: Literal["model_estimate", "DEMO_FIXTURE"] = Field(
        ...,
        description="Data provenance — strictly 'model_estimate'",
    )
