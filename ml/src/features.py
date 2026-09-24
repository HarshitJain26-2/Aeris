"""
AERIS Feature Engineering & Dataset Gating Module (ml/src/features.py)
====================================================================
Implements:
1. Hourly aggregation preserving camera and direction granularity in intermediate tables
2. Spatial zone mapping for Pune traffic intersections with Haversine distance thresholds
3. Unified schema alignment:
   [timestamp, zone_id, latitude, longitude, pm25, pm10, temperature, humidity, wind_speed, rainfall, traffic_count]
4. STRICT GATING: Refuses to produce 'aeris_features.parquet' until a verified PM2.5
   series (either real OpenAQ observations OR explicitly labeled CAMS Global modeled PM2.5)
   is available. Gating message explicitly states source type.
5. ML feature builder: lags, rolling statistics, traffic aggregates, interaction features,
   and time-based train/validation split — with strict no-leakage policy.

ROUND 1 MODELING TARGET:
  CPCB/XKDR/OpenAQ provide no Pune ground-station PM2.5 for Jan 11–18, 2023.
  The verified Round 1 target is CAMS Global modeled PM2.5 from the Open-Meteo
  Air Quality API (domains=cams_global).
  This MUST be labeled 'CAMS Global modeled PM2.5' everywhere.
  It must NEVER be called 'CPCB observed PM2.5', 'ground truth', or 'observed PM2.5'.
"""

import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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
    ingest_cams_global_pm25,
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

    # 4. Assess PM2.5 Source & Model-Ready Gating
    #    Accepts both real CPCB/OpenAQ observations and explicitly labeled CAMS modeled PM2.5.
    #    In both cases the source_type must be present in the data to gate correctly.
    has_any_pm25 = (
        aq_df is not None
        and not aq_df.empty
        and "pm25" in aq_df.columns
        and aq_df["pm25"].notna().sum() > 0
    )

    # Determine source type for gating message
    is_modeled_target = False
    pm25_source_label = "unknown"
    if has_any_pm25 and "source_type" in aq_df.columns:
        source_types = aq_df["source_type"].dropna().unique().tolist()
        is_modeled_target = "modeled" in source_types
        if "source" in aq_df.columns:
            pm25_source_label = aq_df["source"].dropna().iloc[0] if len(aq_df) > 0 else "unknown"

    if not has_any_pm25:
        gate_msg = (
            "GATED: No PM2.5 series is available (neither real ground-station observations "
            "nor verified CAMS Global modeled PM2.5). "
            "In accordance with zero-fabrication and model-readiness rules, 'aeris_features.parquet' "
            "will NOT be generated until a valid PM2.5 source is ingested. "
            "Verified intermediate datasets ('traffic_clean.parquet', 'traffic_hourly.parquet', "
            "'weather_hourly.parquet', 'edgar_pune_context.parquet') have been successfully created."
        )
        logger.warning(gate_msg)
        result_report["status"] = "gated_missing_air_quality"
        result_report["gating_reason"] = gate_msg
        return result_report

    if is_modeled_target:
        logger.info(
            f"CAMS Global modeled PM2.5 verified as Round 1 modeling target "
            f"(source='{pm25_source_label}', source_type='modeled'). "
            "Building unified model-ready dataset. "
            "IMPORTANT: Any validation is temporal holdout against the CAMS modeled target — "
            "NOT against Pune ground-truth observations. "
            "aeris_features.parquet pm25 column is MODELED, NOT CPCB observed."
        )
    else:
        logger.info(
            "Real ground-station PM2.5 observations verified. "
            f"Building unified model-ready dataset (source='{pm25_source_label}')."
        )

    zone_traffic = build_zone_traffic_summary(hourly_traffic)

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

    # Merge PM2.5 data — handling differs by source type:
    #   - CAMS modeled (source_type='modeled'): city-wide target, broadcast to all zones by timestamp.
    #     DO NOT claim this represents three independently observed zones.
    #   - Station observations (source_type='observed' or absent): use zone distance mapping.
    if is_modeled_target:
        # CAMS Global: join by timestamp only (city-wide, not spatially differentiated per zone)
        aq_ts_pm25 = (
            aq_df.groupby("timestamp", as_index=False)[["pm25"]]
            .mean()
        )
        aq_ts_pm25["pm25_source"] = pm25_source_label
        aq_ts_pm25["pm25_source_type"] = "modeled"
        unified = unified.merge(aq_ts_pm25, on="timestamp", how="left")
        unified["pm10"] = np.nan  # CAMS Global does not provide PM10 via this endpoint
        logger.info(
            "CAMS modeled PM2.5 joined city-wide by timestamp. "
            "pm25 column is MODELED (not per-zone observed). "
            "pm10 column set to NaN (not available from CAMS Global endpoint)."
        )
    else:
        mapped_aq = map_air_quality_to_zones(aq_df)
        if not mapped_aq.empty:
            aq_hourly = (
                mapped_aq.groupby(["timestamp", "zone_id"], as_index=False)[["pm25", "pm10"]]
                .mean()
            )
            unified = unified.merge(aq_hourly, on=["timestamp", "zone_id"], how="left")
            unified["pm25_source"] = pm25_source_label
            unified["pm25_source_type"] = "observed"
        else:
            unified["pm25"] = np.nan
            unified["pm10"] = np.nan
            unified["pm25_source"] = "none"
            unified["pm25_source_type"] = "none"

    # Target Unified Schema Order:
    # timestamp, zone_id, latitude, longitude, pm25, pm10, temperature, humidity, wind_speed, rainfall,
    # traffic_count, pm25_source, pm25_source_type
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
        "pm25_source",
        "pm25_source_type",
    ]
    for col in target_schema:
        if col not in unified.columns:
            unified[col] = np.nan
    unified = unified[target_schema]

    # Validate output
    features_path = out_dir / "aeris_features.parquet"
    unified.to_parquet(features_path, index=False)

    result_report["status"] = "success"
    result_report["aeris_features_path"] = str(features_path)
    result_report["row_count"] = len(unified)
    result_report["null_counts"] = unified.isnull().sum().to_dict()
    result_report["pm25_source"] = pm25_source_label
    result_report["pm25_source_type"] = "modeled" if is_modeled_target else "observed"

    logger.info(
        f"Unified feature matrix generated: {features_path} ({len(unified)} rows). "
        f"PM2.5 source: '{pm25_source_label}' (type: {'modeled' if is_modeled_target else 'observed'}). "
        f"Null counts: {result_report['null_counts']}"
    )
    return result_report


# -----------------------------------------------------------------------------
# ML FEATURE BUILDER — LAGS, ROLLING, INTERACTION FEATURES, TIME-BASED SPLIT
# -----------------------------------------------------------------------------
def build_ml_features(
    unified_df: pd.DataFrame,
    pm25_lag_hours: List[int] = [1, 2, 3, 6, 12, 24],
    pm25_rolling_windows: List[int] = [3, 6, 12, 24],
    traffic_rolling_windows: List[int] = [3, 6],
    val_hours: int = 24,
    output_dir: str = "data/processed",
) -> Dict[str, Any]:
    """
    Builds ML-ready feature matrix from the unified AERIS dataset.

    Computes:
    - Lagged PM2.5 features (no future target leakage: lag >= 1 hour only)
    - Rolling mean/std PM2.5 features (shifted to avoid leakage)
    - Lagged and rolling traffic count features
    - Weather features (temperature, humidity, wind_speed, rainfall)
    - Temporal features (hour_of_day, day_of_week, is_weekend)
    - Scientifically defensible interaction features:
        * traffic × wind_speed (dispersion potential)
        * traffic × humidity (hygroscopic aerosol growth proxy)
    - Time-based train/validation split (last val_hours held out)
      NOT random split — temporal ordering is preserved.

    No-Leakage Policy:
    - All PM2.5 lag/rolling features use shift(>=1) so prediction time t
      uses only PM2.5 from t-1 and earlier.
    - Rolling windows are computed on shifted series.
    - Future PM2.5 values are NEVER included in features.

    Validation wording (when PM2.5 source is CAMS modeled):
    - "temporal holdout against the CAMS modeled target"
    - NOT "ground truth validation"

    Args:
        unified_df: Output of build_unified_features() — must contain columns:
                    timestamp, zone_id, pm25, pm25_source_type, traffic_count,
                    temperature, humidity, wind_speed, rainfall.
        pm25_lag_hours: List of lag values (hours) for PM2.5 autoregressive features.
        pm25_rolling_windows: List of window sizes (hours) for PM2.5 rolling stats.
        traffic_rolling_windows: List of window sizes (hours) for traffic rolling stats.
        val_hours: Number of most-recent hours to reserve for validation (time-based split).
        output_dir: Directory to save train/validation parquet splits.

    Returns:
        Dict with:
            - 'train_path': Path to training split parquet
            - 'val_path': Path to validation split parquet
            - 'feature_columns': List of feature column names used
            - 'target_column': 'pm25'
            - 'pm25_source_type': 'modeled' or 'observed'
            - 'val_hours': Number of validation hours
            - 'train_rows': Row count in training split
            - 'val_rows': Row count in validation split
            - 'leakage_check': Description of leakage prevention measures
    """
    if unified_df is None or unified_df.empty:
        logger.warning("build_ml_features: empty input DataFrame.")
        return {}

    # Determine source type for correct validation labeling
    pm25_source_type = "unknown"
    if "pm25_source_type" in unified_df.columns:
        types = unified_df["pm25_source_type"].dropna().unique().tolist()
        pm25_source_type = types[0] if types else "unknown"

    val_label = (
        "temporal holdout against the CAMS modeled target"
        if pm25_source_type == "modeled"
        else "temporal holdout against observed PM2.5"
    )
    logger.info(
        f"Building ML features. PM2.5 source type: '{pm25_source_type}'. "
        f"Validation strategy: {val_label}."
    )

    # Work per zone_id to preserve temporal structure within each zone
    zone_dfs = []
    for zone_id, zone_df in unified_df.groupby("zone_id"):
        df = zone_df.sort_values("timestamp").copy().reset_index(drop=True)

        # --- Temporal features (no leakage: purely calendar) ---
        df["hour_of_day"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

        # --- PM2.5 lag features (shift >= 1 hour: strictly no leakage) ---
        for lag in pm25_lag_hours:
            df[f"pm25_lag_{lag}h"] = df["pm25"].shift(lag)

        # --- PM2.5 rolling features (shift(1) first to avoid leakage at t) ---
        pm25_shifted = df["pm25"].shift(1)
        for window in pm25_rolling_windows:
            df[f"pm25_roll_mean_{window}h"] = pm25_shifted.rolling(window, min_periods=1).mean()
            df[f"pm25_roll_std_{window}h"] = pm25_shifted.rolling(window, min_periods=1).std()

        # --- Traffic rolling features (shift(1) first for consistency) ---
        traffic_shifted = df["traffic_count"].shift(1)
        for window in traffic_rolling_windows:
            df[f"traffic_roll_mean_{window}h"] = traffic_shifted.rolling(window, min_periods=1).mean()

        # --- Scientifically defensible interaction features ---
        # traffic × wind_speed: Higher wind speed disperses traffic emissions.
        # traffic × humidity: Higher humidity enhances hygroscopic particle growth.
        # Both use current-hour traffic and weather (not future PM2.5).
        df["traffic_x_wind"] = df["traffic_count"] * df["wind_speed"]
        df["traffic_x_humidity"] = df["traffic_count"] * df["humidity"]

        zone_dfs.append(df)

    feat_df = pd.concat(zone_dfs, ignore_index=True).sort_values(["timestamp", "zone_id"])

    # --- Time-based train/validation split ---
    # Last val_hours (across all zones) reserved for validation — NO random shuffling.
    all_timestamps = sorted(feat_df["timestamp"].unique())
    if len(all_timestamps) <= val_hours:
        logger.warning(
            f"Dataset has only {len(all_timestamps)} unique timestamps, "
            f"which is <= val_hours={val_hours}. Using last 20% for validation."
        )
        split_idx = max(1, int(len(all_timestamps) * 0.8))
    else:
        split_idx = len(all_timestamps) - val_hours

    train_timestamps = set(all_timestamps[:split_idx])
    val_timestamps = set(all_timestamps[split_idx:])

    train_df = feat_df[feat_df["timestamp"].isin(train_timestamps)].copy()
    val_df = feat_df[feat_df["timestamp"].isin(val_timestamps)].copy()

    logger.info(
        f"Time-based split: {len(train_timestamps)} train timestamps ({len(train_df)} rows), "
        f"{len(val_timestamps)} validation timestamps ({len(val_df)} rows). "
        f"Validation strategy: {val_label}."
    )

    # Identify feature columns (exclude target and metadata)
    non_feature_cols = {
        "timestamp", "zone_id", "latitude", "longitude",
        "pm25",  # target — never a feature
        "pm10",  # secondary target — not used as predictor
        "pm25_source", "pm25_source_type",
    }
    feature_columns = [c for c in feat_df.columns if c not in non_feature_cols]

    # Save split artifacts
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    train_path = out_path / "aeris_ml_train.parquet"
    val_path = out_path / "aeris_ml_val.parquet"
    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    logger.info(f"Train split saved: {train_path} ({len(train_df)} rows).")
    logger.info(f"Validation split saved: {val_path} ({len(val_df)} rows).")

    if pm25_source_type == "modeled":
        logger.info(
            "REMINDER: Validation PM2.5 values are CAMS Global modeled, NOT Pune ground-truth. "
            "Report as 'temporal holdout against the CAMS modeled target'."
        )

    return {
        "train_path": str(train_path),
        "val_path": str(val_path),
        "feature_columns": feature_columns,
        "target_column": "pm25",
        "pm25_source_type": pm25_source_type,
        "val_hours": len(val_timestamps),
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "leakage_check": (
            "All PM2.5 lag/rolling features use shift(>=1). "
            "Rolling windows computed on shifted PM2.5. "
            "Temporal features are calendar-only. "
            "Interaction features use same-hour traffic/weather (not future PM2.5). "
            "Validation split is time-based (last N hours), not random."
        ),
    }


# -----------------------------------------------------------------------------
# 5. CITY-LEVEL FORECASTING DATASET & PERSISTENCE BENCHMARK
# -----------------------------------------------------------------------------
CITY_FEATURE_COLUMNS: List[str] = [
    "temperature",
    "humidity",
    "wind_speed",
    "rainfall",
    "traffic_alankar",
    "traffic_jehangir",
    "traffic_rto",
    "traffic_total",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "pm25_lag_1h",
    "pm25_lag_2h",
    "pm25_lag_3h",
    "pm25_lag_6h",
    "pm25_lag_12h",
    "pm25_lag_24h",
    "pm25_roll_mean_3h",
    "pm25_roll_mean_6h",
    "pm25_roll_mean_12h",
    "pm25_roll_mean_24h",
    "traffic_roll_mean_3h",
    "traffic_roll_mean_6h",
    "traffic_x_wind",
    "traffic_x_humidity",
]

CITY_TARGET_COLUMN: str = "pm25_target_t_plus_1"


def calculate_persistence_baseline(
    actual: Union[pd.Series, np.ndarray, List[float]],
    predicted: Union[pd.Series, np.ndarray, List[float]],
) -> Dict[str, float]:
    """
    Computes MAE and RMSE for a persistence forecast baseline:
        prediction(t+1) = PM2.5(t)

    Args:
        actual: Target values at t+1.
        predicted: Baseline persistence values at t.

    Returns:
        Dict with 'mae' and 'rmse' rounded to 4 decimal places.
    """
    actual_arr = np.asarray(actual, dtype=float)
    pred_arr = np.asarray(predicted, dtype=float)

    valid_mask = ~np.isnan(actual_arr) & ~np.isnan(pred_arr)
    if not np.any(valid_mask):
        return {"mae": float("nan"), "rmse": float("nan")}

    diff = actual_arr[valid_mask] - pred_arr[valid_mask]
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    return {"mae": round(mae, 4), "rmse": round(rmse, 4)}


def build_city_level_ml_dataset(
    traffic_df: Optional[pd.DataFrame] = None,
    weather_df: Optional[pd.DataFrame] = None,
    cams_df: Optional[pd.DataFrame] = None,
    val_split_date: str = "2023-01-18",
    output_dir: str = "data/processed",
) -> Dict[str, Any]:
    """
    Builds a dedicated city-level hourly ML forecasting dataset with exactly ONE ROW PER TIMESTAMP.

    Design Principles:
    - Exactly one row per hourly timestamp (192 rows before filtering).
    - CAMS Global PM2.5 represents the single urban-airshed modeled target for Pune.
    - Three Pune traffic zones are retained as distinct spatial predictors (traffic_alankar,
      traffic_jehangir, traffic_rto) plus total traffic, rather than creating redundant target rows.
    - Target is a genuine 1-hour-ahead forecast: pm25_target_t_plus_1 = PM2.5(t+1).
    - No future-target leakage:
        * PM2.5 lags strictly use t-1 and earlier (pm25_lag_1h is PM2.5 at t-1).
        * Rolling PM2.5 statistics are computed on shifted series (shift(1)).
        * Traffic and weather features come from current hour t (no future data).
        * pm25(t+1) is strictly NOT in the feature matrix.
        * Same-hour PM2.5 is strictly NOT in the feature matrix.
    - Chronological split:
        * Training period: before val_split_date (with complete 24h lag history and valid t+1 target).
        * Validation period: val_split_date (with valid t+1 target).
    - Persistence benchmark: prediction(t+1) = PM2.5(t) evaluated on validation.

    Saves:
        - data/processed/aeris_ml_city.parquet (full 192-hour unpartitioned dataset)
        - data/processed/aeris_ml_city_train.parquet (clean training split)
        - data/processed/aeris_ml_city_val.parquet (clean validation split)

    Returns:
        Dict reporting dataset paths, row counts, feature columns, target column,
        validation metrics for persistence baseline, and leakage audit.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data if not supplied
    if weather_df is None or weather_df.empty:
        w_path = out_dir / "weather_hourly.parquet"
        if w_path.exists():
            weather_df = pd.read_parquet(w_path)
        else:
            raise FileNotFoundError(f"Weather dataset not found at {w_path}")

    if cams_df is None or cams_df.empty:
        c_path = out_dir / "cams_global_pune_pm25_hourly.parquet"
        if c_path.exists():
            cams_df = pd.read_parquet(c_path)
        else:
            raise FileNotFoundError(f"CAMS PM2.5 dataset not found at {c_path}")

    if traffic_df is None or traffic_df.empty:
        t_path = out_dir / "traffic_hourly.parquet"
        if t_path.exists():
            traffic_df = pd.read_parquet(t_path)
        else:
            raise FileNotFoundError(f"Traffic dataset not found at {t_path}")

    # 2. Sort and align chronologically
    weather_sorted = weather_df.sort_values("timestamp").reset_index(drop=True)
    cams_sorted = cams_df.sort_values("timestamp").reset_index(drop=True)
    timestamps = weather_sorted["timestamp"]

    # 3. Aggregate junction-level traffic per timestamp
    # Identify junction / zone column
    j_col = "junction" if "junction" in traffic_df.columns else "zone_id"

    alankar_mask = traffic_df[j_col].astype(str).str.contains("Alankar", case=False)
    jehangir_mask = traffic_df[j_col].astype(str).str.contains("Jehangir", case=False)
    rto_mask = traffic_df[j_col].astype(str).str.contains("RTO", case=False)

    traffic_alankar = (
        traffic_df[alankar_mask]
        .groupby("timestamp")["traffic_count"]
        .sum()
        .reindex(timestamps, fill_value=0.0)
        .values
    )
    traffic_jehangir = (
        traffic_df[jehangir_mask]
        .groupby("timestamp")["traffic_count"]
        .sum()
        .reindex(timestamps, fill_value=0.0)
        .values
    )
    traffic_rto = (
        traffic_df[rto_mask]
        .groupby("timestamp")["traffic_count"]
        .sum()
        .reindex(timestamps, fill_value=0.0)
        .values
    )
    traffic_total = traffic_alankar + traffic_jehangir + traffic_rto

    # 4. Target: 1-hour-ahead forecast pm25(t+1)
    pm25_raw = pd.Series(cams_sorted["pm25"].values)
    pm25_target_t_plus_1 = pm25_raw.shift(-1).values

    # 5. Build base city table
    city_df = pd.DataFrame({
        "timestamp": timestamps,
        "pm25_target_t_plus_1": pm25_target_t_plus_1,
        "pm25_current": pm25_raw.values,  # kept for persistence evaluation; excluded from feature matrix
        "temperature": weather_sorted["temperature"].values,
        "humidity": weather_sorted["humidity"].values,
        "wind_speed": weather_sorted["wind_speed"].values,
        "rainfall": weather_sorted["rainfall"].values,
        "traffic_alankar": traffic_alankar,
        "traffic_jehangir": traffic_jehangir,
        "traffic_rto": traffic_rto,
        "traffic_total": traffic_total,
    })

    # Calendar features (purely deterministic, no leakage)
    city_df["hour_of_day"] = city_df["timestamp"].dt.hour
    city_df["day_of_week"] = city_df["timestamp"].dt.dayofweek
    city_df["is_weekend"] = (city_df["day_of_week"] >= 5).astype(int)

    # 6. PM2.5 Lags: strictly t-1 and earlier
    # pm25_lag_1h is PM2.5 at t-1 (strictly 1 hour before feature timestamp t, 2 hours before target t+1)
    for lag in [1, 2, 3, 6, 12, 24]:
        city_df[f"pm25_lag_{lag}h"] = pm25_raw.shift(lag).values

    # 7. PM2.5 Rolling Means: on shifted series (strictly t-1 and earlier)
    pm25_shifted = pm25_raw.shift(1)
    for window in [3, 6, 12, 24]:
        city_df[f"pm25_roll_mean_{window}h"] = pm25_shifted.rolling(window).mean().values

    # 8. Traffic Rolling Means: on hour t and earlier (traffic_total)
    traffic_series = pd.Series(traffic_total)
    city_df["traffic_roll_mean_3h"] = traffic_series.rolling(3, min_periods=1).mean().values
    city_df["traffic_roll_mean_6h"] = traffic_series.rolling(6, min_periods=1).mean().values

    # 9. Physical Interaction Features (hour t traffic x hour t weather)
    city_df["traffic_x_wind"] = city_df["traffic_total"] * city_df["wind_speed"]
    city_df["traffic_x_humidity"] = city_df["traffic_total"] * city_df["humidity"]

    # Source metadata
    city_df["pm25_source"] = "CAMS Global Atmospheric Composition Forecasts"
    city_df["pm25_source_type"] = "modeled"

    # Save full 192-hour unpartitioned city dataset
    full_city_path = out_dir / "aeris_ml_city.parquet"
    city_df.to_parquet(full_city_path, index=False)
    logger.info(f"Saved full city ML dataset to {full_city_path} ({len(city_df)} rows).")

    # 10. Chronological Train/Validation Partition
    # Training period: timestamps < val_split_date with complete 24h lag history and valid t+1 target
    train_mask = (
        (city_df["timestamp"] < val_split_date)
        & city_df["pm25_lag_24h"].notna()
        & city_df["pm25_target_t_plus_1"].notna()
    )
    train_df = city_df[train_mask].copy().reset_index(drop=True)

    # Validation period: timestamps >= val_split_date with valid t+1 target
    val_mask = (
        (city_df["timestamp"] >= val_split_date)
        & city_df["pm25_target_t_plus_1"].notna()
    )
    val_df = city_df[val_mask].copy().reset_index(drop=True)

    # Save partitioned datasets
    train_path = out_dir / "aeris_ml_city_train.parquet"
    val_path = out_dir / "aeris_ml_city_val.parquet"
    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    logger.info(f"Saved city ML train split to {train_path} ({len(train_df)} rows).")
    logger.info(f"Saved city ML val split to {val_path} ({len(val_df)} rows).")

    # 11. Compute Persistence Baseline on Validation: prediction(t+1) = PM2.5(t)
    persistence_metrics = calculate_persistence_baseline(
        actual=val_df["pm25_target_t_plus_1"],
        predicted=val_df["pm25_current"],
    )
    logger.info(
        f"Validation Persistence Baseline: MAE = {persistence_metrics['mae']:.4f} ug/m3, "
        f"RMSE = {persistence_metrics['rmse']:.4f} ug/m3."
    )

    return {
        "status": "success",
        "city_parquet_path": str(full_city_path),
        "train_path": str(train_path),
        "val_path": str(val_path),
        "feature_columns": CITY_FEATURE_COLUMNS,
        "target_column": CITY_TARGET_COLUMN,
        "total_rows_raw": len(city_df),
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "train_range": (
            str(train_df["timestamp"].min()),
            str(train_df["timestamp"].max()),
        ),
        "val_range": (
            str(val_df["timestamp"].min()),
            str(val_df["timestamp"].max()),
        ),
        "persistence_baseline": persistence_metrics,
        "pm25_source": "CAMS Global Atmospheric Composition Forecasts",
        "pm25_source_type": "modeled",
        "leakage_check": (
            "Target is strictly pm25(t+1). "
            "PM2.5 lag features strictly use t-1 and earlier. "
            "Rolling PM2.5 features computed on shifted series. "
            "Traffic and weather features strictly from hour t. "
            "pm25_target_t_plus_1 and pm25_current are excluded from feature matrix. "
            "Chronological validation split; zero random shuffling."
        ),
    }


if __name__ == "__main__":
    import json
    logger.info("Executing end-to-end feature pipeline (Round 1: CAMS Global modeled PM2.5 target)...")

    # Step A: Ingest Weather & Clean
    raw_weather = ingest_open_meteo()
    clean_w, audit_w = clean_weather_data(raw_weather)

    # Step B: Clean Traffic via Streaming
    hourly_t, audit_t = clean_traffic_stream()

    # Step C: Ingest CAMS Global modeled PM2.5 (Round 1 target)
    cams_result = ingest_cams_global_pm25()
    logger.info(f"CAMS Global ingestion: {json.dumps(cams_result, indent=2, default=str)}")

    if cams_result.get("status") == "success":
        cams_df = pd.read_parquet(cams_result["processed_path"])
    else:
        cams_df = None

    # Step D: Extract EDGAR spatial context (annual, no hourly values generated)
    extract_edgar_pune_context()

    # Step E: Product A — Zone/Digital-Twin Feature Engineering (3 zones, 576 rows)
    report = build_unified_features(
        traffic_df=hourly_t,
        weather_df=clean_w,
        aq_df=cams_df,
    )
    logger.info(f"Pipeline Execution Report (Product A - Zone):\n{json.dumps(report, indent=2, default=str)}")

    # Step F: Product B — City-Level Forecasting ML Dataset (1 row per hour, 1-hour-ahead target)
    city_report = build_city_level_ml_dataset(
        traffic_df=hourly_t,
        weather_df=clean_w,
        cams_df=cams_df,
    )
    logger.info(f"City ML Dataset Report (Product B - Forecasting):\n{json.dumps(city_report, indent=2, default=str)}")
