# AERIS Data Sources & Ingestion Specifications

This document provides complete, transparent specifications for all public datasets integrated into **AERIS — Urban Environmental Digital Twin** (HackMatrix 5.0, Problem Statement: ENR-01) for the pilot study area of **Pune, India**.

---

## 1. Heterogeneous Traffic Count Dataset, Pune (Jan 2023)

### Overview & Attribution
- **Dataset Name**: Heterogeneous Traffic Count Dataset, Pune (Jan 2023)
- **Source Organization**: COEP Technological University Pune, Department of Computer Engineering
- **Authors**: Ashwini Matange & Jibi Abraham
- **Data Provider**: Traffic Police Commissioner, Pune
- **Citation**: Matange, A., & Abraham, J. (2026). Heterogeneous Traffic Count Dataset, Pune (Jan 2023). Mendeley Data, V1.
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Archive Path**: `data/raw/traffic/traffic.zip`

### Geographic Scope & Sensors
- **Target City**: Pune, Maharashtra, India
- **Monitored Intersections (Chowks)**:
  1. **Alankar Chowk** (approx. 18.5284° N, 73.8741° E): Monitored by 2 cameras (`a2`, `a3`).
  2. **Jehangir Chowk** (approx. 18.5310° N, 73.8775° E): Monitored by 3 cameras (`j1`, `j2`, `j3`).
  3. **RTO Chowk** (approx. 18.5314° N, 73.8648° E): Monitored by 3 cameras (`r1`, `r2`, `r3`).
- Each camera represents a fixed CCTV perspective installed at a specific approach of the junction.

### Inventory of Discovered Files
The dataset archive contains exactly **115 CSV files** structured hierarchically by junction and camera:
- `traffic/AlankarChowk/`:
  - `a2/`: 16 files (`a2_11.csv`, `a2_11_one.csv`, ..., `a2_18.csv`, `a2_18_one.csv`)
  - `a3/`: 16 files (`a3_11.csv`, `a3_11_one.csv`, ..., `a3_18.csv`, `a3_18_one.csv`)
- `traffic/JehangirChowk/`:
  - `j1/`: 16 files (`j1_11.csv`, `j1_11_one.csv`, ..., `j1_18.csv`, `j1_18_one.csv`)
  - `j2/`: 16 files (`j2_11.csv`, `j2_11_one.csv`, ..., `j2_18.csv`, `j2_18_one.csv`)
  - `j3/`: 11 files (`j3_11.csv` to `j3_18.csv`, with `_one.csv` present on days 14, 15, 16)
- `traffic/RTOChowk/`:
  - `r1/`: 16 files (`r1_11.csv`, `r1_11_one.csv`, ..., `r1_18.csv`, `r1_18_one.csv`)
  - `r2/`: 16 files (`r2_11.csv`, `r2_11_one.csv`, ..., `r2_18.csv`, `r2_18_one.csv`)
  - `r3/`: 8 files (`r3_11.csv` to `r3_18.csv`, no continuation files needed)

### Raw Schema & Semantics
All 115 files share an identical column schema:

| Column | Raw Type | Unit | Allowed Values | Source Data Dictionary Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `Time` | String | 24-hr clock | `00:00:00`–`23:59:59` | Start timestamp of the aggregation interval |
| `Direction` | String | Categorical | `UP`, `DOWN`, `LEFT`, `RIGHT` | Movement vector relative to the camera frame |
| `car` | Integer | Vehicle count | $\ge 0$ | Cars detected and counted in interval/direction |
| `motorbike` | Integer | Vehicle count | $\ge 0$ | Two-wheelers detected and counted in interval/direction |
| `bus` | Integer | Vehicle count | $\ge 0$ | Buses detected and counted in interval/direction |
| `truck` | Integer | Vehicle count | $\ge 0$ | Trucks detected and counted in interval/direction |

### Empirical Properties & Traceability
1. **Timestamp Resolution & Sub-Second Logging**: Timestamps are truncated to `HH:MM:SS`. Individual rows correspond to video processing samples. Vehicle counts change within identical seconds (e.g. 486 count increments inside the same second in `a2_11.csv`). Naive duplicate dropping would corrupt detection transitions.
2. **Cumulative Counter Sessions**: Within each contiguous recording file, counts for each direction start at 0 and are monotonically non-decreasing over the recording session.
3. **Session Reset on Continuation Files**: When a recording exceeds the file row limit (~$1,048,575$ rows), an extension file (`_one.csv`) is created. In continuation files, the counter restarts from 0.
4. **Camera Independence Rule**: Until camera fields of view are proven to be non-overlapping approaches, camera streams **must not be naively summed**. The pipeline preserves camera-level (`camera_id`) and direction-level (`direction`) counts.

---

## 2. Open-Meteo Historical Weather Dataset

### Overview & Attribution
- **Dataset Name**: Open-Meteo Historical Weather API
- **Source**: Open-Meteo (reanalysis models including ERA5, ERA5-Land, and national meteorological services)
- **Official URL**: [https://archive-api.open-meteo.com/v1/archive](https://archive-api.open-meteo.com/v1/archive)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Authentication**: None required (open public access)

### Geographic Scope & Parameters
- **Location**: Pune, India (Latitude: 18.5204° N, Longitude: 73.8567° E)
- **Timezone**: `Asia/Kolkata` (Indian Standard Time, UTC+05:30)
- **Temporal Resolution**: 1-hour intervals
- **Coverage Period**: 11 January 2023 – 18 January 2023 (configurable to arbitrary historical dates)

### Variables Used & Units
| Source Variable | Aeris Feature Name | Units | Physical Bounds | Description |
| :--- | :--- | :--- | :--- | :--- |
| `temperature_2m` | `temperature` | °C | $[-10, 60]$ | Ambient air temperature at 2 meters above ground |
| `relative_humidity_2m` | `humidity` | % | $[0, 100]$ | Relative humidity at 2 meters above ground |
| `wind_speed_10m` | `wind_speed` | km/h | $[0, 200]$ | Wind speed at 10 meters above ground |
| `precipitation` | `rainfall` | mm | $[0, 500]$ | Total precipitation (rain/showers) during the hour |

### Preprocessing & Validation
- Hourly timestamps parsed to ISO 8601 with `Asia/Kolkata` timezone context.
- Range checks ensure 100% physically valid values. Missing records (if any) are flagged.

---

## 3. Ambient Air Quality Dataset (OpenAQ API v3)

### Overview & Attribution
- **Dataset Name**: OpenAQ Platform API v3
- **Source**: Aggregated government air quality stations from Central Pollution Control Board (CPCB) and IITM SAFAR
- **Official URL**: [https://api.openaq.org/v3](https://api.openaq.org/v3)
- **License**: Open Data Commons Attribution License (ODC-By) / CPCB Open Government Data
- **Authentication**: Requires API key passed in `X-API-Key` header.
- **Environment Variable**: `OPENAQ_API_KEY` (strictly managed via `.env`, never committed)

### Discovered Monitoring Stations in Pune
OpenAQ indexes several active Continuous Ambient Air Quality Monitoring Stations (CAAQMS) across the Pune urban cluster:
1. **Shivajinagar (Revenue Colony / IITM SAFAR)**: ~18.531° N, 73.845° E (~2.0 km west of RTO Chowk)
2. **Hadapsar (IITM SAFAR)**: ~18.508° N, 73.926° E (~6.5 km southeast)
3. **Karve Road (MPCB)**: ~18.507° N, 73.829° E (~5.2 km southwest)
4. **Katraj Dairy (MPCB)**: ~18.457° N, 73.864° E (~8.2 km south)
5. **Bhosari (IITM SAFAR)**: ~18.627° N, 73.847° E (~10.8 km north)
6. **Savitribai Phule Pune University (MPCB)**: ~18.553° N, 73.825° E (~4.8 km northwest)

### Target Variables
- `pm25`: Particulate Matter $\le 2.5\,\mu\text{m}$ ($\mu\text{g/m}^3$)
- `pm10`: Particulate Matter $\le 10\,\mu\text{g/m}^3$ ($\mu\text{g/m}^3$)

### Spatial Mapping & Distance Threshold Strategy
- Stations are matched to traffic intersection zones using a Euclidean / Haversine distance threshold of **5.0 km**.
- The nearest station to the three central chowks is **Shivajinagar** (~2.0 km from RTO Chowk, ~3.0 km from Jehangir Chowk).
- Stations exceeding the 5 km threshold (e.g., Bhosari, Katraj) remain distinct and are **not** forced into the traffic zones.

### Current Access Status & Gating
- Because `OPENAQ_API_KEY` is not currently set in the local environment, the ingestion client gracefully reports that execution is blocked pending credentials.
- **Strict Quality Rule**: No synthetic or fabricated air quality numbers are created. Generating the model-ready dataset (`aeris_features.parquet`) is gated until real OpenAQ observations are successfully ingested.

---

## 4. EDGAR Industrial NetCDF Emissions (v8.1 FT2022)

### Overview & Attribution
- **Dataset Name**: Emissions Database for Global Atmospheric Research (EDGAR) v8.1 Air Pollutants
- **Source**: European Commission, Joint Research Centre (JRC)
- **Official URL**: [https://edgar.jrc.ec.europa.eu/dataset_ap81](https://edgar.jrc.ec.europa.eu/dataset_ap81)
- **License**: European Commission Open Data Policy / JRC Conditions of Use
- **Archive Path**: `data/raw/edgar/` (extracted from `IND_emi_nc.zip`)

### NetCDF Metadata & Variables
- **Files**: 53 NetCDF files (`v8.1_FT2022_AP_PM2.5_1970_IND_emi.nc` to `..._2022_IND_emi.nc`)
- **Dimensions**: `lat: 1800`, `lon: 3600`
- **Coordinates**:
  - `lat`: float64 $[-89.95, 89.95]$ at 0.1° grid spacing (~11 km)
  - `lon`: float64 $[-179.95, 179.95]$ at 0.1° grid spacing (~11 km)
- **Target Variable**: `emissions`
  - Long name: Combustion for manufacturing (`IND` sector)
  - Substance: `PM2.5`
  - Units: **Tonnes per grid cell per year**
  - Temporal Resolution: **Annual total**

### Spatial Extraction for Pune
- Pune Bounding Box: Latitude $[18.35^\circ, 18.65^\circ]\,\text{N}$, Longitude $[73.65^\circ, 74.05^\circ]\,\text{E}$.
- For the central Pune grid cell (`lat=18.55, lon=73.85`), annual industrial combustion emissions were **1,329.56 Tonnes PM2.5** in 2022.

### Temporal Disaggregation Policy
- **No Hourly Industrial Values**: Because EDGAR represents an annual regional aggregate terminating in 2022, creating hourly synthetic values for January 2023 would violate scientific integrity.
- EDGAR is retained strictly as **annual spatial background context** and is excluded from the hourly multi-modal feature set.
