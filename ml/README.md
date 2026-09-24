# AERIS Machine Learning & Data Pipeline (`ml/`)

This directory houses the ingestion, cleaning, and feature engineering workflows for **AERIS — Urban Environmental Digital Twin** (Problem Statement: ENR-01).

---

## 1. Environment Setup & Dependency Installation

### Create & Activate Virtual Environment
```bash
# From repository root
python -m venv .venv

# On Windows (PowerShell)
.venv\Scripts\Activate.ps1

# On Linux / macOS
source .venv/bin/activate
```

### Install Dependencies
```bash
pip install -r ml/requirements.txt
```

---

## 2. API Key Configuration (OpenAQ)

OpenAQ API v3 strictly requires an API key in the `X-API-Key` HTTP header.
To configure the key:
1. Copy the example environment template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and insert your API key:
   ```
   OPENAQ_API_KEY=your_actual_api_key_here
   ```
3. Never hardcode or commit API keys. The `.gitignore` file automatically excludes `.env`.

> [!NOTE]
> If `OPENAQ_API_KEY` is not provided, the ingestion module safely logs a blocker message and prevents downstream generation of ungrounded or synthetic air quality data.

---

## 3. Running the Pipeline

### Step 1: Ingestion
Fetches weather from Open-Meteo, reads raw traffic CSVs from `data/raw/traffic/`, checks OpenAQ, and extracts EDGAR spatial context:
```bash
python ml/src/ingest.py
```
- Weather raw data is saved to `data/raw/weather/open_meteo_pune_2023-01-11_2023-01-18.json`.
- EDGAR regional context is saved to `data/processed/edgar_pune_context.parquet`.

### Step 2: Cleaning & Validation
Validates physical ranges, parses timestamps into `Asia/Kolkata` context, and computes session-aware vehicle deltas while preserving camera-level and direction-level granularity:
```bash
python -c "
from ml.src.ingest import ingest_open_meteo, ingest_traffic, ingest_openaq
from ml.src.clean import clean_weather_data, clean_traffic_data, clean_air_quality_data

raw_w = ingest_open_meteo()
df_w, audit_w = clean_weather_data(raw_w)

raw_t = ingest_traffic()
df_t, audit_t = clean_traffic_data(raw_t)

aq_res = ingest_openaq()
df_aq, audit_aq = clean_air_quality_data(aq_res.get('data_path'))
print('Audits complete:', audit_w, audit_t, audit_aq)
"
```

### Step 3: Feature Engineering & Dataset Gating
Executes the end-to-end multi-modal pipeline:
```bash
python ml/src/features.py
```

### Strict Gating Behavior
- **Intermediate Assets**: Produces verified, reproducible intermediate tables:
  - `data/processed/traffic_clean.parquet`: Clean records preserving `camera_id` and `direction`.
  - `data/processed/traffic_hourly.parquet`: Hourly aggregated counts per junction, camera, and approach.
  - `data/processed/weather_hourly.parquet`: Hourly validated meteorological parameters.
  - `data/processed/edgar_pune_context.parquet`: Annual macro-level industrial emissions grid.
  - `data/processed/cams_global_pune_pm25_hourly.parquet`: Verified 192-hour modeled PM2.5 target (`source_type='modeled'`).
- **Model-Ready Dataset Gating**:
  - `data/processed/aeris_features.parquet` is gated: it will **ONLY** be created when a verified PM2.5 series is present (either authentic ground-station observations or explicitly labeled CAMS Global modeled PM2.5).
  - When CAMS Global modeled PM2.5 is used, the gating and metadata explicitly record `pm25_source_type='modeled'`. It is never labeled as CPCB ground truth.
  - Zero synthetic or fabricated data is injected.

### Step 4: ML Feature Engineering — Two Distinct Data Products
The pipeline generates two distinct data products:

#### Product A: Zone Digital-Twin Dataset (`aeris_features.parquet`)
- **Structure**: 3 Pune junctions (`PUNE_ALANKAR_CHOWK`, `PUNE_JEHANGIR_CHOWK`, `PUNE_RTO_CHOWK`) $\times$ 192 hours = 576 rows.
- **Purpose**: Map visualization, junction-level traffic monitoring, localized source attribution, and interactive scenario simulations.
- **Target Context**: CAMS provides one modeled urban-airshed PM2.5 value per hourly grid point. It is therefore used as the city-level modeled target. Three Pune traffic zones are retained as spatial predictors/context rather than treated as independent PM2.5 observations.

#### Product B: City-Level Hourly Forecasting Dataset (`aeris_ml_city.parquet`)
- **Structure**: Exactly ONE row per hourly timestamp (192 raw hours).
- **Target**: Genuine 1-hour-ahead forecast target `pm25_target_t_plus_1 = PM2.5(t+1)`.
- **Feature Set** (25 predictors):
  - Current-hour weather: `temperature`, `humidity`, `wind_speed`, `rainfall` (hour $t$).
  - Current-hour junction traffic: `traffic_alankar`, `traffic_jehangir`, `traffic_rto`, `traffic_total` (hour $t$).
  - Calendar attributes: `hour_of_day`, `day_of_week`, `is_weekend`.
  - PM2.5 autoregressive lags strictly from $t-1$ and earlier: `pm25_lag_1h`, `2h`, `3h`, `6h`, `12h`, `24h`.
  - Shifted PM2.5 rolling averages: `pm25_roll_mean_3h`, `6h`, `12h`, `24h`.
  - Traffic rolling averages: `traffic_roll_mean_3h`, `6h`.
  - Physical interaction terms: `traffic_x_wind`, `traffic_x_humidity`.
  - Zero target leakage: neither `pm25_target_t_plus_1` nor same-hour `pm25(t)` appears in the feature matrix.
- **Chronological Partition**:
  - `data/processed/aeris_ml_city_train.parquet`: 144 hours (2023-01-12 00:00 to 2023-01-17 23:00, after 24h lag requirement). Zero nulls.
  - `data/processed/aeris_ml_city_val.parquet`: 23 hours (2023-01-18 00:00 to 2023-01-18 22:00, excluding last hour with missing $t+1$). Zero nulls.
- **Persistence Baseline Benchmark**:
  - Predicts $\text{prediction}(t+1) = \text{PM2.5}(t)$.
  - Evaluated on validation period: MAE = 7.2217 $\mu\text{g/m}^3$, RMSE = 11.1196 $\mu\text{g/m}^3$.
  - Evaluation wording policy: **"temporal holdout against the CAMS modeled target"** (not ground truth).

---

## 4. Expected Unified Output Schema

The unified schema of `data/processed/aeris_features.parquet` is strictly:

| Field Name | Type | Physical Unit | Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | `datetime64[ns, Asia/Kolkata]` | ISO Datetime | Start of hourly aggregation interval |
| `zone_id` | `string` | Categorical ID | Standardized zone (e.g. `PUNE_ALANKAR_CHOWK`) |
| `latitude` | `float64` | Decimal Degrees | Latitude of intersection |
| `longitude` | `float64` | Decimal Degrees | Longitude of intersection |
| `pm25` | `float64` | $\mu\text{g/m}^3$ | Ambient PM2.5 concentration (modeled or mapped observation) |
| `pm10` | `float64` | $\mu\text{g/m}^3$ | Ambient PM10 concentration (NaN when using CAMS Global) |
| `temperature` | `float64` | °C | Ambient 2m air temperature |
| `humidity` | `float64` | % | Relative humidity |
| `wind_speed` | `float64` | km/h | 10m wind speed |
| `rainfall` | `float64` | mm | Hourly precipitation |
| `traffic_count` | `float64` | Vehicles / hour | Total vehicles observed across intersection approaches |
| `pm25_source` | `string` | Categorical | Specific source product (e.g. `CAMS Global Atmospheric Composition Forecasts`) |
| `pm25_source_type` | `string` | Categorical | Data classification: `modeled` or `observed` |

---

## 5. Verification & Testing

Run all unit and integration tests with `pytest`:
```bash
pytest -v
```
Tests verify timestamp parsing, session-aware counter delta math, camera/direction preservation, Open-Meteo range validation, Haversine distance thresholding, OpenAQ missing key handling, CAMS Global 192-hour parsing and validation, modeled-vs-observed labeling, leak-free feature construction, XGBoost evaluation metrics reproducibility, and counterfactual scenario mechanics.

---

## 6. Counterfactual Scenario Engine (`ml/src/scenario.py`)

The scenario engine provides reproducible model-based what-if traffic intervention simulations:
- **Intervention Mechanics**: Scales current-hour traffic predictors (`traffic_alankar`, `traffic_jehangir`, `traffic_rto`, `traffic_total`, `traffic_x_wind`, `traffic_x_humidity`) by $(1 - \text{reduction\_pct} / 100)$.
- **Fixed Context**: Historical traffic context (`traffic_roll_mean_3h`, `traffic_roll_mean_6h`), weather covariates, PM2.5 autoregressive history, and calendar features remain strictly unmodified.
- **Scientific Limitation**:
  > *"The scenario engine perturbs current-hour traffic predictors only. Historical traffic context remains fixed. Because the forecasting model is predictive rather than causal, the learned counterfactual response may be non-monotonic and should not be interpreted as a guaranteed physical effect."*

