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
- **Model-Ready Dataset Gating**:
  - `data/processed/aeris_features.parquet` will **ONLY** be created when genuine OpenAQ PM2.5/PM10 observations are present.
  - Zero synthetic data is injected.

---

## 4. Expected Unified Output Schema

When real OpenAQ observations are merged, the unified schema of `data/processed/aeris_features.parquet` is strictly:

| Field Name | Type | Physical Unit | Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | `datetime64[ns, Asia/Kolkata]` | ISO Datetime | Start of hourly aggregation interval |
| `zone_id` | `string` | Categorical ID | Standardized zone (e.g. `PUNE_ALANKAR_CHOWK`) |
| `latitude` | `float64` | Decimal Degrees | Latitude of intersection |
| `longitude` | `float64` | Decimal Degrees | Longitude of intersection |
| `pm25` | `float64` | $\mu\text{g/m}^3$ | Ambient PM2.5 concentration from mapped CAAQMS |
| `pm10` | `float64` | $\mu\text{g/m}^3$ | Ambient PM10 concentration from mapped CAAQMS |
| `temperature` | `float64` | °C | Ambient 2m air temperature |
| `humidity` | `float64` | % | Relative humidity |
| `wind_speed` | `float64` | km/h | 10m wind speed |
| `rainfall` | `float64` | mm | Hourly precipitation |
| `traffic_count` | `float64` | Vehicles / hour | Total vehicles observed across intersection approaches |

---

## 5. Verification & Testing

Run all unit and integration tests with `pytest`:
```bash
pytest -v
```
Tests verify timestamp parsing, session-aware counter delta math, camera/direction preservation, Open-Meteo range validation, Haversine distance thresholding, OpenAQ missing key handling, and strict dataset gating.
