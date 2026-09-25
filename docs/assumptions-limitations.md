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

### Missing Traffic Measurements Policy
- **Zero-Imputation Mandate**: Missing vehicle count measurements (`NaN` / `null`) are **never** filled with zero (`fillna(0)` is strictly forbidden). Treating missing measurements as zero vehicles causes severe false delta spikes when counters resume (e.g. $[100, \text{NaN}, 101]$ filled with 0 would produce an artificial delta of $+101$).
- **Safe Exclusion & Audit**:
  - Missing measurement rows are detected and logged in the audit record (`missing_count_rows_dropped`).
  - Rows with missing vehicle counts are excluded *prior* to computing deltas.
  - When non-monotonic resets occur within a session (e.g., $v_t < v_{t-1}$), the step delta is set to $0.0$ to prevent fabricated deltas.

### First-Row Session Baseline Policy
- **Baseline Establishment**: The first row of any recording session establishes the measurement baseline.
- **Delta Definition**: The first row is assigned $\Delta v_0 = 0.0$ rather than being counted as $v_0$ vehicles passing at $t_0$. This prevents fabricating initial vehicle surges when cameras begin logging at non-zero counters.
- **Session Boundary Definition**: `session_file` defines the boundary. Continuation files (`_one.csv`) are independent sessions and do not inherit prior counter values.

### Unified Canonical Traffic Cleaning
- Both batch/non-streaming (`clean_traffic_data`) and streaming (`clean_traffic_stream`) invoke the identical canonical session cleaner (`clean_traffic_session`). Streaming processing yields bit-identical results to batch processing on the same dataset.

### Source-Row Order Preservation for Sub-Second Observations
- **Sub-Second Frequency**: CCTV traffic logs record multiple detection updates within the identical second (timestamps truncated to `HH:MM:SS`).
- **Ordering Guarantee**: To prevent indeterminacy or delta corruption from unstable sorting, each CSV recording is indexed with a private source-order identifier (`_source_row`) upon ingestion.
- **Deterministic Sort**: `clean_traffic_session` sorts by `["Direction", "timestamp", "_source_row"]`, ensuring same-second observations maintain their authentic physical chronology and compute strictly correct incremental deltas.

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

---

## 5. Weather Quality & Strict Exclusion (Zero Silent Clipping)

### Physical Bound Enforcement
- Weather features from Open-Meteo are validated against physical plausibility ranges:
  - `temperature`: $[-10.0^\circ\text{C}, 60.0^\circ\text{C}]$
  - `humidity`: $[0.0\%, 100.0\%]$
  - `wind_speed`: $[0.0\,\text{km/h}, 200.0\,\text{km/h}]$
  - `rainfall`: $[0.0\,\text{mm}, 500.0\,\text{mm}]$

### Exclusion vs. Clipping
- **Strict Prohibition of Silent Clipping**: Out-of-bounds readings (e.g. an erroneous $85^\circ\text{C}$ sensor spike) are **never clipped** to boundary thresholds (such as $60^\circ\text{C}$). Clipping silently introduces fabricated synthetic values into the training distribution.
- **Audit Logging & Drop**: Any record violating physical boundaries is flagged, recorded with its exact violation reason in the data cleaning audit (`invalid_rows_dropped`), and excluded from the clean dataset.

---

## 6. Universal Timezone Alignment (`Asia/Kolkata`)

### Timezone Canonicalization
To guarantee temporal synchronization across multi-modal data streams:
1. **Traffic Streams**: Raw CCTV logs are recorded in Indian Standard Time (IST, UTC+05:30). Timestamps are localized as timezone-aware `Asia/Kolkata`.
2. **Weather Time Series**: Open-Meteo feeds are requested with `timezone=Asia/Kolkata` or converted directly to `Asia/Kolkata`.
3. **OpenAQ Observations**: Ingested UTC ISO 8601 timestamps are parsed and converted to `Asia/Kolkata` (`tz_convert("Asia/Kolkata")`).
4. **Consistency Enforcement**: All joins, resamplings, and feature alignments operate on timezone-aware `Asia/Kolkata` hourly periods.

## 7. CAMS Global Modeled PM2.5 - Round 1 Target and Limitations

### A. CPCB/XKDR/OpenAQ Jan 11-18 2023 Observation Gap
- All 9 genuine Pune CPCB CAAQM stations return zero PM2.5 measurements for Jan 11-18, 2023 from XKDR, OpenAQ, and the CPCB bulk CSV dataset (2010-2023, MH001-MH041).
- The simultaneous resumption of data across all stations on Jan 19-20 is consistent with coordinated instrument maintenance, not a dataset deficiency.
- Consequence: The traffic window (Jan 11-18, 2023) has no real Pune PM2.5 observations from any institutional source.

### B. CAMS Global Modeled PM2.5 Substitution
- Decision: CAMS Global Atmospheric Composition Forecasts is used as the Round 1 modeling target for Jan 11-18, 2023.
- Justification: It is the only complete, gapless, non-fabricated 192-hour PM2.5 series for Pune in this window.
- Labeling mandate: source_type=modeled, source=CAMS Global Atmospheric Composition Forecasts in every artifact.
- NEVER call this CPCB observed PM2.5, ground truth, or observed PM2.5.

### C. CAMS Spatial Resolution Limitation
- Grid resolution: ~0.4 degrees (~40 km). Nearest grid point: 18.5 N, 73.9 E.
- CAMS PM2.5 is a broad urban/regional airshed estimate, NOT a localized junction measurement.
- Design rule: CAMS PM2.5 is joined by timestamp only and NOT duplicated as three independently observed zone values.

### D. No Ground-Truth Validation for Jan 11-18 2023
- All model evaluation is reported as: temporal holdout against the CAMS modeled target
- NOT ground truth validation. NOT CPCB observed performance.

### E. EDGAR Annual-Only Limitation
- EDGAR v8.1 FT2022 provides annual regional PM2.5 industrial combustion totals only.
- No diurnal profile, no hourly disaggregation, no 2023 data.
- EDGAR is excluded from the hourly feature matrix. Hourly industrial values are NEVER synthesized from EDGAR.

### F. Distinction Between Observed, Modeled, and Scenario Data
- Observed (CPCB/OpenAQ): source_type=observed. Ground truth. Unavailable for target window.
- Modeled (CAMS Global): source_type=modeled. Round 1 PM2.5 target.
- Scenario (future): source_type=scenario. Counterfactual/intervention analysis.
- Annual context (EDGAR): excluded from features. Spatial industrial background only.

## 8. Dual Data Products: Zone Digital-Twin vs. City Forecasting Dataset

### Distinct Architectural Roles
1. **Product A: Zone Digital-Twin Dataset (`aeris_features.parquet`)**:
   - Scope: 3 junctions (`PUNE_ALANKAR_CHOWK`, `PUNE_JEHANGIR_CHOWK`, `PUNE_RTO_CHOWK`) x 192 hours = 576 rows.
   - Purpose: Geospatial map rendering, junction-specific traffic visualization, localized driver attribution, and counterfactual scenario simulations.
   - Target Representation: CAMS provides one modeled urban-airshed PM2.5 value per hourly grid point. It is therefore used as the city-level modeled target. Three Pune traffic zones are retained as spatial predictors/context rather than treated as independent PM2.5 observations.

2. **Product B: Hourly City-Level ML Forecasting Dataset (`aeris_ml_city.parquet`, `_train.parquet`, `_val.parquet`)**:
   - Scope: Exactly ONE row per hourly timestamp (192 raw hours).
   - Training split: 144 hours (2023-01-12 00:00 to 2023-01-17 23:00, after 24h lag requirement).
   - Validation split: 23 hours (2023-01-18 00:00 to 2023-01-18 22:00, excluding last hour which has no t+1 target).
   - Target Definition: Genuine 1-hour-ahead forecast target `pm25_target_t_plus_1 = PM2.5(t+1)`.
   - Feature Matrix Structure:
     * Current-hour weather (`temperature`, `humidity`, `wind_speed`, `rainfall` at hour t).
     * Current-hour junction-level traffic (`traffic_alankar`, `traffic_jehangir`, `traffic_rto`, `traffic_total` at hour t).
     * PM2.5 lags strictly from t-1 and earlier (`pm25_lag_1h` .. `pm25_lag_24h`).
     * Rolling PM2.5 averages computed on shifted series (`pm25_roll_mean_*`).
     * Zero future-target leakage: neither `pm25(t+1)` nor same-hour `pm25(t)` appears in the feature matrix.
   - Persistence Baseline Benchmark:
     * `prediction(t+1) = PM2.5(t)` evaluated on validation period.

### Scientific Taxonomy of Data Types
- **Observed Traffic**: Camera-level vehicle counts derived from real Pune CCTV recordings (Jan 11-18, 2023).
- **Observed/Reanalysis Weather**: Open-Meteo historical ERA5 meteorological variables for Pune center.
- **Modeled CAMS PM2.5**: Gridded atmospheric-composition model output (~40 km resolution) used as city-level forecast target; NEVER called ground truth.
- **Scenario Outputs**: Simulated counterfactual outcomes under hypothetical policy/traffic interventions.

## 9. Counterfactual Scenario Simulation Limitations

### Current-Hour Perturbation Semantics
The scenario engine perturbs current-hour traffic predictors only (`traffic_alankar`, `traffic_jehangir`, `traffic_rto`, `traffic_total`, `traffic_x_wind`, `traffic_x_humidity`). Historical traffic context (`traffic_roll_mean_3h`, `traffic_roll_mean_6h`) remains fixed because an intervention beginning at hour t cannot rewrite past history.

### Predictive vs. Causal Model Behavior
The scenario engine perturbs current-hour traffic predictors only. Historical traffic context remains fixed. Because the forecasting model is predictive rather than causal, the learned counterfactual response may be non-monotonic and should not be interpreted as a guaranteed physical effect.

### Scenario Simulation Endpoint (`POST /api/scenario/simulate`)
- **Input Contract**: `traffic_reduction_pct` (numeric, validated `0 <= value <= 50`).
- **Output Contract**:
  - `baseline_pm25`: model-estimated baseline PM2.5 forecast without intervention (~68.0 µg/m³).
  - `scenario_pm25`: model-estimated scenario PM2.5 forecast under specified reduction.
  - `delta`: model-estimated change `scenario_pm25 - baseline_pm25` (µg/m³).
  - `traffic_reduction_pct`: percentage reduction evaluated.
  - `dataSource`: strictly labeled as `model_estimate`.
- **Identity at 0%**: At 0% traffic reduction, `scenario_pm25` equals `baseline_pm25` within normal floating-point tolerance (`delta = 0.0`).
- **Non-Monotonicity Disclosure**: Evaluated sensitivity reveals minor non-monotonic responses at 50% traffic reduction (`delta = +0.3199 µg/m³`) due to tree split boundaries on interaction features. This behavior is preserved and reported truthfully without smoothing or heuristic overrides.
