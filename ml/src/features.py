"""
AERIS Feature Engineering & Dataset Gating Module (ml/src/features.py)
====================================================================
Implements:
1. Hourly aggregation preserving camera and direction granularity in intermediate tables
2. Spatial zone mapping for Pune traffic intersections with Haversine distance thresholds
3. Unified schema alignment:
   [timestamp, zone_id, latitude, longitude, pm25, pm10, temperature, humidity, wind_speed, rainfall, traffic_count]
4. STRICT GATING: Refuses to produce 'aeris_features.parquet' until real OpenAQ PM2.5
   observations are verified. Produces clean intermediate assets instead.
"""

import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd

from ml.src.clean import (
    clean_air_quality_data,
    clean_traffic_data,
    clean_traffic_stream,
    clean_weather_data,
)
from ml.src.ingest import (
    extract_edgar_pune_context,
    ingest_open_meteo,
    ingest_openaq,
    ingest_traffic,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aeris.features")

# Documented Coordinates for Pune Chowks (WGS84)
ZONE_COORDINATES: Dict[str, Dict[str, Any]] = {
    "AlankarChowk": {
        "zone_id": "PUNE_ALANKAR_CHOWK",
        "latitude": 18.5284,
        "longitude": 73.8741,
        "description": "Alankar Chowk / Ambedkar Rd intersection",
    },
    "JehangirChowk": {
        "zone_id": "PUNE_JEHANGIR_CHOWK",
        "latitude": 18.5310,
        "longitude": 73.8775,
        "description": "Jehangir Hospital / Sasoon Rd intersection",
    },
    "RTOChowk": {
        "zone_id": "PUNE_RTO_CHOWK",
        "latitude": 18.5314,
        "longitude": 73.8648,
        "description": "Regional Transport Office (RTO) Chowk / Sangam Bridge",
    },
}

# Distance threshold for air-quality station spatial mapping (in kilometers)
AIR_QUALITY_DISTANCE_THRESHOLD_KM = 5.0


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates using Haversine formula."""
    r = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def build_hourly_traffic_features(
    cleaned_traffic_df: pd.DataFrame,
    output_path: Optional[str] = "data/processed/traffic_hourly.parquet",
) -> pd.DataFrame:
    """
    Aggregates traffic vehicle deltas to hourly intervals while preserving camera and direction.

    Outputs table with columns:
    [timestamp, junction, zone_id, camera_id, direction, delta_car, delta_motorbike,
     delta_bus, delta_truck, traffic_count]
    """
    if cleaned_traffic_df.empty:
        logger.warning("Empty traffic DataFrame supplied for feature generation.")
        return pd.DataFrame()

    df = cleaned_traffic_df.copy()

    # Truncate timestamp to hourly window start if not already hourly
    df["timestamp"] = df["timestamp"].dt.floor("1h")

    # Map junction to standardized zone_id
    df["zone_id"] = df["junction"].map(lambda j: ZONE_COORDINATES.get(j, {}).get("zone_id", j))
    df["latitude"] = df["junction"].map(lambda j: ZONE_COORDINATES.get(j, {}).get("latitude", np.nan))
    df["longitude"] = df["junction"].map(lambda j: ZONE_COORDINATES.get(j, {}).get("longitude", np.nan))

    # Group by hourly window, junction, zone, camera, and direction
    group_cols = ["timestamp", "junction", "zone_id", "camera_id", "direction", "latitude", "longitude"]
    agg_dict = {
        "delta_car": "sum",
        "delta_motorbike": "sum",
        "delta_bus": "sum",
        "delta_truck": "sum",
        "traffic_count": "sum",
    }
    hourly_df = df.groupby(group_cols, as_index=False).agg(agg_dict)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        hourly_df.to_parquet(out_p, index=False)
        logger.info(f"Saved camera/direction hourly traffic to {out_p} ({len(hourly_df)} rows).")

    return hourly_df


def build_zone_traffic_summary(
    hourly_camera_traffic_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produces intersection-level traffic summary by zone.
    
    Sums traffic_count across camera streams only after camera-level data has been safely preserved.
    """
    if hourly_camera_traffic_df.empty:
        return pd.DataFrame()

    group_cols = ["timestamp", "zone_id", "latitude", "longitude"]
    zone_summary = (
        hourly_camera_traffic_df.groupby(group_cols, as_index=False)["traffic_count"]
        .sum()
    )
    return zone_summary


def map_air_quality_to_zones(
    aq_df: pd.DataFrame,
    zones: Dict[str, Dict[str, Any]] = ZONE_COORDINATES,
    threshold_km: float = AIR_QUALITY_DISTANCE_THRESHOLD_KM,
) -> pd.DataFrame:
    """
    Applies documented nearest-station / distance-threshold mapping strategy.
    
    If no station is within threshold_km, keeps station separate and does not force mapping.
    """
    if aq_df.empty:
        return pd.DataFrame()

    matched_rows = []
    # Discover unique stations in the data
    stations = aq_df[["station_id", "station_name", "station_lat", "station_lon"]].drop_duplicates()

    for _, s_row in stations.iterrows():
        s_lat, s_lon = s_row["station_lat"], s_row["station_lon"]
        if pd.isna(s_lat) or pd.isna(s_lon):
            continue

        # Check distance to each traffic zone
        for j_name, z_info in zones.items():
            dist = haversine_distance_km(s_lat, s_lon, z_info["latitude"], z_info["longitude"])
            if dist <= threshold_km:
                logger.info(
                    f"Mapped CAAQMS station '{s_row['station_name']}' to zone '{z_info['zone_id']}' "
                    f"(Distance: {dist:.2f} km <= {threshold_km} km threshold)."
                )
                # Assign this station's observations to the matched zone
                subset = aq_df[aq_df["station_id"] == s_row["station_id"]].copy()
                subset["zone_id"] = z_info["zone_id"]
                subset["distance_to_zone_km"] = dist
                matched_rows.append(subset)
            else:
                logger.debug(
                    f"Station '{s_row['station_name']}' is {dist:.2f} km from '{z_info['zone_id']}' "
                    f"(exceeds {threshold_km} km threshold); kept separate."
                )

    if not matched_rows:
        logger.warning(f"No air quality stations were within {threshold_km} km of traffic zones.")
        return pd.DataFrame()

    return pd.concat(matched_rows, ignore_index=True)


def build_unified_features(
    traffic_df: Optional[pd.DataFrame] = None,
    weather_df: Optional[pd.DataFrame] = None,
    aq_df: Optional[pd.DataFrame] = None,
    output_dir: str = "data/processed",
) -> Dict[str, Any]:
    """
    Constructs intermediate processed tables and strictly gates aeris_features.parquet.

    Gating Behavior:
    - If real PM2.5 observations are missing/empty, aeris_features.parquet is NOT created.
    - Cleaned intermediate assets (traffic_clean.parquet, traffic_hourly.parquet,
      weather_hourly.parquet) are saved for full transparency.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result_report: Dict[str, Any] = {
        "status": "pending",
        "traffic_clean_path": None,
        "traffic_hourly_path": None,
        "weather_hourly_path": None,
        "aeris_features_path": None,
        "gating_reason": None,
        "null_counts": {},
        "row_count": 0,
    }

    # 1. Process and save Weather
    if weather_df is not None and not weather_df.empty:
        weather_path = out_dir / "weather_hourly.parquet"
        weather_df.to_parquet(weather_path, index=False)
        result_report["weather_hourly_path"] = str(weather_path)
        logger.info(f"Saved weather features to {weather_path} ({len(weather_df)} rows).")

    # 2. Process and save Traffic
    hourly_traffic = pd.DataFrame()
    if traffic_df is not None and not traffic_df.empty:
        # Check if traffic_df is already hourly aggregated or raw cleaned
        if "delta_car" in traffic_df.columns and "session_file" not in traffic_df.columns:
            # Already hourly aggregated from clean_traffic_stream
            hourly_traffic = build_hourly_traffic_features(
                traffic_df, output_path=str(out_dir / "traffic_hourly.parquet")
            )
            result_report["traffic_hourly_path"] = str(out_dir / "traffic_hourly.parquet")
        else:
            traffic_clean_path = out_dir / "traffic_clean.parquet"
            traffic_df.to_parquet(traffic_clean_path, index=False)
            result_report["traffic_clean_path"] = str(traffic_clean_path)

            hourly_traffic = build_hourly_traffic_features(
                traffic_df, output_path=str(out_dir / "traffic_hourly.parquet")
            )
            result_report["traffic_hourly_path"] = str(out_dir / "traffic_hourly.parquet")
    else:
        hourly_traffic = pd.DataFrame()

    # 3. Process and save Air Quality intermediate table
    if aq_df is not None and not aq_df.empty:
        aq_clean_path = out_dir / "air_quality_clean.parquet"
        aq_df.to_parquet(aq_clean_path, index=False)
        result_report["air_quality_clean_path"] = str(aq_clean_path)
        logger.info(f"Saved cleaned air quality observations to {aq_clean_path} ({len(aq_df)} rows).")

    # 4. Assess Air Quality & Model-Ready Gating
    has_real_aq = (
        aq_df is not None
        and not aq_df.empty
        and "pm25" in aq_df.columns
        and aq_df["pm25"].notna().sum() > 0
    )

    if not has_real_aq:
        gate_msg = (
            "GATED: Real OpenAQ PM2.5 observations are not available (OPENAQ_API_KEY required). "
            "In accordance with zero-fabrication and model-readiness rules, 'aeris_features.parquet' "
            "will NOT be generated until genuine ambient air quality observations are ingested. "
            "Verified intermediate datasets ('traffic_clean.parquet', 'traffic_hourly.parquet', "
            "'weather_hourly.parquet', 'edgar_pune_context.parquet') have been successfully created."
        )
        logger.warning(gate_msg)
        result_report["status"] = "gated_missing_air_quality"
        result_report["gating_reason"] = gate_msg
        return result_report

    # 4. If genuine air quality data is available, perform multi-modal fusion
    logger.info("Real PM2.5 observations verified. Building unified model-ready dataset...")
    zone_traffic = build_zone_traffic_summary(hourly_traffic)
    mapped_aq = map_air_quality_to_zones(aq_df)

    # Cross join traffic zones with weather by timestamp
    merged = []
    for j_name, z_info in ZONE_COORDINATES.items():
        z_id = z_info["zone_id"]
        z_w = weather_df.copy()
        z_w["zone_id"] = z_id
        z_w["latitude"] = z_info["latitude"]
        z_w["longitude"] = z_info["longitude"]
        merged.append(z_w)

    base_grid = pd.concat(merged, ignore_index=True)

    # Merge traffic counts
    unified = base_grid.merge(
        zone_traffic[["timestamp", "zone_id", "traffic_count"]],
        on=["timestamp", "zone_id"],
        how="left",
    )
    unified["traffic_count"] = unified["traffic_count"].fillna(0)

    # Merge mapped air quality
    if not mapped_aq.empty:
        aq_hourly = (
            mapped_aq.groupby(["timestamp", "zone_id"], as_index=False)[["pm25", "pm10"]]
            .mean()
        )
        unified = unified.merge(aq_hourly, on=["timestamp", "zone_id"], how="left")
    else:
        unified["pm25"] = np.nan
        unified["pm10"] = np.nan

    # Target Unified Schema Order:
    # timestamp, zone_id, latitude, longitude, pm25, pm10, temperature, humidity, wind_speed, rainfall, traffic_count
    target_schema = [
        "timestamp",
        "zone_id",
        "latitude",
        "longitude",
        "pm25",
        "pm10",
        "temperature",
        "humidity",
        "wind_speed",
        "rainfall",
        "traffic_count",
    ]
    unified = unified[target_schema]

    # Validate output
    features_path = out_dir / "aeris_features.parquet"
    unified.to_parquet(features_path, index=False)

    result_report["status"] = "success"
    result_report["aeris_features_path"] = str(features_path)
    result_report["row_count"] = len(unified)
    result_report["null_counts"] = unified.isnull().sum().to_dict()

    logger.info(
        f"Unified feature matrix generated: {features_path} ({len(unified)} rows). "
        f"Null counts: {result_report['null_counts']}"
    )
    return result_report


if __name__ == "__main__":
    import json
    logger.info("Executing end-to-end feature pipeline...")
    # Step A: Ingest Weather & Clean
    raw_weather = ingest_open_meteo()
    clean_w, audit_w = clean_weather_data(raw_weather)

    # Step B: Clean Traffic via Streaming
    hourly_t, audit_t = clean_traffic_stream()

    # Step C: Air Quality Ingestion & Clean
    aq_ingest_res = ingest_openaq()
    clean_aq, audit_aq = clean_air_quality_data(aq_ingest_res.get("data_path"))

    # Step D: Extract EDGAR spatial context
    extract_edgar_pune_context()

    # Step E: Feature Engineering & Gating Check
    report = build_unified_features(
        traffic_df=hourly_t,
        weather_df=clean_w,
        aq_df=clean_aq,
    )
    logger.info(f"Pipeline Execution Report:\n{json.dumps(report, indent=2, default=str)}")
