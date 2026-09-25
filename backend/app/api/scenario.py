"""
Scenario API Router
Exposes POST /api/scenario/simulate
"""
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.scenario import ScenarioRequest, ScenarioResponse
from backend.app.services.scenario_service import ScenarioService, get_scenario_service

router = APIRouter()


@router.post(
    "/simulate",
    response_model=ScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate traffic reduction counterfactual scenario",
    description=(
        "Simulates a model-based counterfactual traffic reduction scenario (0-50%) for Pune "
        "using the trained XGBoost model. Perturbs direct current-hour traffic predictors "
        "while strictly preserving historical context (traffic rolling averages, PM2.5 lags) "
        "and meteorological variables.\n\n"
        "**Scientific Disclosure & Limitation**: The forecasting model is predictive rather than causal. "
        "Scenario changes represent model estimates under the specified traffic reduction and should not "
        "be interpreted as guaranteed physical outcomes. Because the model learns tree-based boundaries, "
        "the counterfactual response may be non-monotonic."
    ),
)
def simulate_traffic_reduction(
    request: ScenarioRequest,
    service: ScenarioService = Depends(get_scenario_service),
) -> ScenarioResponse:
    """
    Executes real XGBoost counterfactual scenario simulation.
    Returns baseline PM2.5, scenario PM2.5, and delta.
    """
    try:
        return service.simulate(traffic_reduction_pct=request.traffic_reduction_pct)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
