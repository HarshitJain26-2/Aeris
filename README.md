# AERIS
## Urban Environmental Intelligence & Digital Twin

### Problem
Conventional air-quality monitoring systems primarily show current pollution levels but provide limited support for evaluating how modeled interventions may affect future pollution levels.

### Proposed Solution
AERIS is an Urban Environmental Digital Twin that combines air-quality, weather, traffic, and environmental data to forecast pollution and simulate intervention scenarios for **Pune, India**.

---

### Core Round 1 Demo Flow

```
Observed / Available Data (Pune Central Telemetry)
  │
  ▼
Interactive Digital Twin Map (Alankar, Jehangir, RTO Chowks)
  │
  ▼
Zone Selection & Hotspot Telemetry
  │
  ▼
1-Hour PM2.5 Forecast (XGBoost Forecaster with 90% CI)
  │
  ▼
Model Driver Attribution (SHAP Feature Importances)
  │
  ▼
Counterfactual Scenario Simulation (0–50% Traffic Volume Reduction)
  │
  ▼
Modeled Scenario Outcome (Baseline vs. Scenario Delta & Percent Impact)
  │
  ▼
Historical Validation Evidence (Temporal Holdout vs. Persistence Baseline)
```

---

### Scientific & Provenance Integrity

1. **Target Provenance**: Due to a verified institutional sensor offline period across Pune CAAQMS stations during Jan 11–18, 2023, the model target is **CAMS Global Atmospheric Composition Forecasts** (modeled atmospheric PM2.5, `source_type=modeled`). It is strictly **not** described as ground-truth sensor measurements.
2. **Forecast Horizon**: The forecaster provides a genuine **1-hour-ahead forecast ($t+1$)** without future target leakage.
3. **Model Validation**: On the unseen 23-hour temporal holdout split (Jan 18, 2023), the XGBoost model achieves:
   - **MAE**: $5.65\,\mu\text{g/m}^3$ (vs Persistence $7.22\,\mu\text{g/m}^3$ → **21.8% error reduction**)
   - **RMSE**: $7.90\,\mu\text{g/m}^3$ (vs Persistence $11.12\,\mu\text{g/m}^3$ → **28.9% error reduction**)
   - **$R^2$**: $0.8885$
4. **Scenario Simulation**: Counterfactual traffic reduction (0–50%) perturbs current-hour traffic predictors only, strictly fixing historical traffic context. Outputs are labeled as predictive model estimates, not physical causal measurements.

---

### Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, MapLibre GL, Recharts, Lucide Icons
- **Backend**: FastAPI, Pydantic v2, Uvicorn
- **Machine Learning**: XGBoost, scikit-learn, SHAP, NumPy, Pandas
- **Data Engineering**: Parquet, DuckDB, Open-Meteo, CAMS, COEP CCTV Traffic Logs

---

### Quick Start: Running the Full Demo

#### 1. Start the Backend API (FastAPI)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Swagger Docs: `http://127.0.0.1:8000/docs`*

#### 2. Start the Frontend Dashboard (React + Vite)
```powershell
cd frontend
npm run dev
```
*Access UI at: `http://localhost:5173`*

#### 3. Run Automated Verification Tests
```powershell
# Backend / ML Test Suite (146 tests)
pytest -q

# Frontend Checks
cd frontend
npm run typecheck
npm run lint
npm run build
```

---

### Team
- Harshit Jain
- Rushikesh Ambhore
- Pranav Dawage
- Bhavik Chhoriya