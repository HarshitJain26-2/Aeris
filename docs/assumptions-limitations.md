# AERIS Data Assumptions, Methodological Decisions & Limitations

This document records architectural decisions, alignment strategies, empirical observations, and limitations for **AERIS — Urban Environmental Digital Twin** (Problem Statement: ENR-01).

---

## 1. Traffic Data Engineering Decisions

### Camera & Direction Independence Rule
- **Decision**: Traffic counts are preserved at **camera-level (`camera_id`)** and **direction-level (`direction`)** before any spatial aggregation.
- **Rationale**: The dataset provides CCTV streams across 8 cameras (`a2, a3, j1, j2, j3, r1, r2, r3`) at 3 junctions. Without field-of-view ground truth proving cameras observe mutually exclusive approaches, naively summing counts across all cameras at a chowk would risk double-counting vehicles moving across overlapping camera fields.
- **Traceability**: Processed datasets retain:
  - `junction` (e.g. `AlankarChowk`)
  - `camera_id` (e.g. `a2`)
  - `direction` (e.g. `UP`, `DOWN`, `LEFT`, `RIGHT`)
  - `session_file` (e.g. `a2_11.csv`)

### Counter Monotonicity & Continuation Resets
- **Empirical Observation**: Within each contiguous CSV recording, vehicle counters are monotonically non-decreasing from zero. When a continuation file (`_one.csv`) starts, the software counter resets to 0.
- **Handling**: 
  - Interval deltas are calculated per `(junction, camera_id, direction, session_file)`.
  - Continuation files are treated as independent recording segments, preventing artificial negative spikes or undercounts.
  - Step deltas $\Delta v_t = v_t - v_{t-1}$ are verified $\ge 0$.

### Temporal Window Handling
- **Observation**: Source files in this archive capture morning traffic sessions ranging from `08:59:19` to `12:02:48` between 11 and 18 January 2023.
- **Handling**: We do not enforce an artificial "fixed 09:00–12:00" window. The aggregation logic groups by flexible time buckets (e.g. hourly or 15-minute) and accurately reports intervals where camera coverage was active.

---

## 2. Spatial Alignment Strategy & Distance Thresholds

### Pilot City & Zone Representation
- **Target Intersections**:
  - `PUNE_ALANKAR_CHOWK`: Lat 18.5284° N, Lon 73.8741° E
  - `PUNE_JEHANGIR_CHOWK`: Lat 18.5310° N, Lon 73.8775° E
  - `PUNE_RTO_CHOWK`: Lat 18.5314° N, Lon 73.8648° E
- **Weather Alignment**:
  - Open-Meteo weather parameters (temperature, humidity, wind speed, rainfall) are retrieved for the central Pune coordinates (18.5204° N, 73.8567° E). At the urban scale, meteorology is treated as uniform across the three closely situated central junctions (all within ~1.5 km of each other).

### Air Quality Monitoring Station Mapping
- **Identified Pune Stations**:
  - `Shivajinagar (IITM SAFAR)`: ~18.531° N, 73.845° E (Distance to RTO Chowk: ~2.1 km; Jehangir: ~3.5 km; Alankar: ~3.1 km)
  - `Hadapsar (IITM SAFAR)`: ~18.508° N, 73.926° E (Distance: ~6.5 km)
  - `Karve Road (MPCB)`: ~18.507° N, 73.829° E (Distance: ~5.2 km)
  - `Bhosari (IITM SAFAR)`: ~18.627° N, 73.847° E (Distance: ~10.8 km)
- **Distance Threshold Policy**:
  - A maximum distance threshold of **5.0 km** is enforced.
  - Intersections within 5.0 km of an active CAAQMS station (such as Shivajinagar) map to that station's observations.
  - Stations exceeding the 5.0 km threshold are **kept separate** to avoid misrepresenting localized microclimate and dispersion dynamics.

---

## 3. Industrial Emissions (EDGAR) Policy

### Annual Context vs. Hourly Time Series
- **EDGAR Specifications**:
  - Substance: PM2.5, Sector: `IND` (Combustion for manufacturing)
  - Spatial Grid: 0.1° × 0.1° (~11 km)
  - Temporal Frequency: **Annual total emissions** (1970–2022)
- **Scientific Decision**:
  - EDGAR provides valuable macro-level spatial context: the Pune center grid cell produced **1,329.56 Tonnes of PM2.5** in 2022.
  - However, EDGAR lacks diurnal profiles, hourly variations, and 2023 data.
  - **Rule**: We **never** fabricate hourly industrial activity values from annual EDGAR data. It is maintained strictly as spatial background context in `data/processed/edgar_pune_context.parquet` and excluded from the hourly multi-modal feature matrix.

---

## 4. Strict Gating Policy for Model-Ready Features

### OpenAQ Dependency & Blocker Handling
- Live air quality data requires authentication with `OPENAQ_API_KEY`.
- In the absence of an API key in the execution environment:
  - **No Fake Data**: We strictly refuse to inject synthetic, interpolated, or dummy PM2.5/PM10 readings.
  - **Dataset Gating**: The model-ready feature file (`data/processed/aeris_features.parquet`) is **gated and will not be created** until real OpenAQ observations are successfully ingested and validated.
  - **Intermediate Processing**: Real, validated intermediate datasets (`traffic_clean.parquet`, `traffic_hourly.parquet`, `weather_hourly.parquet`) are produced so downstream data pipelines remain verifiable without false assertions.
