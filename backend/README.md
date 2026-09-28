# AERIS Backend Service

FastAPI environmental intelligence backend for **AERIS — Urban Environmental Digital Twin & Forecasting Platform** (Pilot city: Pune, India).

## Endpoints Summary

| Method | Endpoint | Description | Provenance |
| :--- | :--- | :--- | :--- |
| `GET` | `/health`, `/api/health` | Service health status | Operational |
| `GET` | `/api/v1/zones` | Monitored Pune junction zones & CCTV stream metadata | Documented Ground Truth |
| `GET` | `/api/v1/current` | Observed/available air quality & weather telemetry | Sensor Telemetry / Fixture |
| `GET` | `/api/v1/forecast` | Genuine 1-hour-ahead PM2.5 model forecast (`horizonHours = 1`) with 90% CI | `model_estimate` |
| `GET` | `/api/v1/drivers` | SHAP feature attribution breakdown across urban drivers | `model_estimate` |
| `POST` | `/api/scenario/simulate`<br>`/api/v1/scenario` | What-if counterfactual traffic reduction simulation (0–50%) via trained XGBoost | `model_estimate` |
| `GET` | `/api/v1/model/validation` | Historical validation evidence, persistence baseline benchmarks, and holdout sample | Empirical Holdout Metrics |

## Scientific & Provenance Disclosures

1. **Target Provenance**: The PM2.5 target is based on CAMS Global Atmospheric Composition Forecasts (modeled atmospheric concentration). It is **not** ground-station sensor observations due to a coordinated CPCB instrument maintenance gap during Jan 11–18, 2023.
2. **Forecast Horizon**: The XGBoost forecaster provides a genuine 1-hour-ahead forecast ($t+1$).
3. **Scenario Engine**: Counterfactual simulations perturb current-hour traffic volume while strictly preserving historical context. The model is predictive rather than causal.

## Running Locally

```powershell
# From repository root
cd backend

# Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# Start FastAPI server on port 8000
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation (Swagger UI) is available at: `http://127.0.0.1:8000/docs`
