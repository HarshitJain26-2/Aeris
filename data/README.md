# AERIS Data Architecture & Registry

This directory contains raw and processed data assets for **AERIS — Urban Environmental Digital Twin** (HackMatrix 5.0, Problem Statement: ENR-01), focusing on the pilot city of **Pune, India**.

## Directory Structure

```
data/
├── raw/
│   ├── air_quality/         # Real ambient PM2.5/PM10 observations (OpenAQ API v3)
│   ├── weather/             # Hourly historical weather parameters (Open-Meteo)
│   ├── traffic/             # Heterogeneous Traffic Count Dataset, Pune (CCTV / YOLO)
│   └── edgar/               # EDGAR v8.1 global NetCDF atmospheric pollutant emissions
├── processed/
│   ├── traffic_clean.parquet    # Cleaned, session-aware camera & direction level traffic
│   ├── traffic_hourly.parquet   # Hourly aggregated traffic by junction, camera, and direction
│   ├── weather_hourly.parquet   # Cleaned, timezone-aligned hourly weather for Pune
│   └── aeris_features.parquet   # Unified multi-modal feature matrix (GATED pending real AQ data)
└── README.md
```

## Storage & Git Tracking Policy

To ensure repository efficiency and prevent accidental commits of large datasets:
- **Raw and Processed Storage**: Raw archive files (`.zip`, `.nc`), intermediate arrays, and generated `.parquet` files are explicitly excluded via `.gitignore`.
- **Directory Preservation**: Subdirectory structures are tracked via `.gitkeep` files.
- **Reproducibility**: All raw datasets are ingested and transformed via scripts under `ml/src/`. No manual file editing is permitted.

## Source Data Registry Summary

| Dataset Identifier | Domain | Source Organization | Geographic Scope | Temporal Coverage | Native Resolution | Storage Path |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenAQ Pune** | Air Quality | CPCB / IITM SAFAR via OpenAQ API v3 | Pune, India (Station network) | Configurable / Jan 2023 | 15-min to 1-hour | `data/raw/air_quality/` |
| **Open-Meteo Pune** | Meteorology | ECMWF / ERA5 / Global Models via Open-Meteo | Pune (18.5204° N, 73.8567° E) | 11–18 Jan 2023 | 1-hour | `data/raw/weather/` |
| **Heterogeneous Traffic Pune** | Urban Mobility | COEP Tech Univ / Pune Traffic Police | 3 Junctions (Alankar, Jehangir, RTO) | 11–18 Jan 2023 | Per-frame / 1-sec | `data/raw/traffic/` |
| **EDGAR v8.1 IND PM2.5** | Industrial Context | European Commission, JRC | Global Grid (0.1° × 0.1°) | 1970–2022 (Annual) | 0.1° (~11 km) | `data/raw/edgar/` |

Detailed source descriptions, coordinate mappings, data dictionaries, and preprocessing workflows are documented in [`docs/data-sources.md`](../docs/data-sources.md). Data assumptions, limitations, and gating rules are maintained in [`docs/assumptions-limitations.md`](../docs/assumptions-limitations.md).
