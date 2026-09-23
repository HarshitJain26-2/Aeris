"""
AERIS Data Cleaning & Validation Module (ml/src/clean.py)
=========================================================
Implements robust, auditable data cleaning for:
1. Heterogeneous Traffic Dataset (session-aware counter processing)
2. Open-Meteo Weather observations
3. OpenAQ Air Quality observations

Enforces:
- Traceability of raw-source semantics
- Preservation of camera-level and direction-level traffic granularity
- Explicit logging of rows audited, modified, or removed
- Zero data fabrication
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aeris.clean")


# -----------------------------------------------------------------------------
# 1. TRAFFIC DATA CLEANING
# -----------------------------------------------------------------------------
def clean_traffic_data(
    raw_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw traffic observations while preserving camera and direction independence.

    Empirical Rationale:
    - CCTV recordings contain monotonically non-decreasing cumulative counts per session file.
    - Software counters reset to 0 in continuation files (_one.csv).
    - Rows capture frame-level detections; counts increment within identical seconds.
    - We compute step deltas per (junction, camera_id, session_file, Direction) so that
      interval sums yield exact vehicle counts without frame-rate assumptions or double counting.

    Args:
        raw_df: Raw traffic DataFrame from ingest_traffic().

    Returns:
        Tuple of (cleaned_df, audit_metrics_dict).
    """
    audit: Dict[str, Any] = {
        "initial_rows": len(raw_df),
        "dropped_null_rows": 0,
        "invalid_timestamps": 0,
        "invalid_negative_counts": 0,
        "final_valid_rows": 0,
    }

    if raw_df.empty:
        logger.warning("Empty DataFrame passed to clean_traffic_data.")
        return pd.DataFrame(), audit

    df = raw_df.copy()

    # Drop rows where all measurement fields are null
    req_cols = ["Time", "Direction", "car", "motorbike", "bus", "truck"]
    before_drop = len(df)
    df = df.dropna(subset=req_cols, how="all")
    audit["dropped_null_rows"] = before_drop - len(df)

    # Validate and standardize Direction
    valid_directions = {"UP", "DOWN", "LEFT", "RIGHT"}
    df["Direction"] = df["Direction"].astype(str).str.strip().str.upper()
    df = df[df["Direction"].isin(valid_directions)]

    # Parse timestamps combining date and Time
    # Expected format: '2023-01-11 09:00:34' in Asia/Kolkata
    datetime_str = df["date"] + " " + df["Time"].astype(str)
    parsed_timestamps = pd.to_datetime(datetime_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    
    invalid_time_mask = parsed_timestamps.isna()
    audit["invalid_timestamps"] = int(invalid_time_mask.sum())
    if audit["invalid_timestamps"] > 0:
        logger.warning(f"Dropping {audit['invalid_timestamps']} rows with invalid timestamps.")
        df = df[~invalid_time_mask]
        parsed_timestamps = parsed_timestamps[~invalid_time_mask]

    # Assign timezone-aware timestamp
    df["timestamp"] = parsed_timestamps.dt.tz_localize("Asia/Kolkata", ambiguous="NaT", nonexistent="shift_forward")

    # Validate non-negative integer counts
    count_cols = ["car", "motorbike", "bus", "truck"]
    for c in count_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        neg_mask = df[c] < 0
        if neg_mask.any():
            audit["invalid_negative_counts"] += int(neg_mask.sum())
            df.loc[neg_mask, c] = 0

    # Sort deterministically by session, approach, and time
    sort_cols = ["junction", "camera_id", "session_file", "Direction", "timestamp"]
    df = df.sort_values(sort_cols).reset_index(drop=True)

    # Session-aware vehicle delta calculation
    # Within each session file and direction, compute step-by-step non-negative changes
    group_cols = ["junction", "camera_id", "session_file", "Direction"]
    grouped = df.groupby(group_cols)

    for c in count_cols:
        delta_col = f"delta_{c}"
        # diff() yields NaN on first row of each session; fill with the first row's baseline value
        df[delta_col] = grouped[c].diff().fillna(df[c])
        # Clip any abnormal negative jumps (e.g. if file had internal reset)
        df[delta_col] = df[delta_col].clip(lower=0)

    # Calculate total traffic count for this row (step delta sum)
    df["traffic_count"] = (
        df["delta_car"] + df["delta_motorbike"] + df["delta_bus"] + df["delta_truck"]
    )

    # Standardize column naming and preserve raw source values alongside deltas
    cleaned_df = df[[
        "timestamp",
        "junction",
        "camera_id",
        "Direction",
        "session_file",
        "car",
        "motorbike",
        "bus",
        "truck",
        "delta_car",
        "delta_motorbike",
        "delta_bus",
        "delta_truck",
        "traffic_count",
    ]].rename(columns={
        "Direction": "direction",
        "car": "car_raw",
        "motorbike": "motorbike_raw",
        "bus": "bus_raw",
        "truck": "truck_raw",
    })

    audit["final_valid_rows"] = len(cleaned_df)
    audit["total_vehicles_counted"] = float(cleaned_df["traffic_count"].sum())
    audit["active_junctions"] = cleaned_df["junction"].unique().tolist()
    audit["active_cameras"] = cleaned_df["camera_id"].unique().tolist()

    logger.info(
        f"Traffic cleaning complete: {audit['final_valid_rows']} valid rows retained from "
        f"{audit['initial_rows']} initial rows. Total vehicles detected: {audit['total_vehicles_counted']:.0f}."
    )
    return cleaned_df, audit


def clean_traffic_stream(
    traffic_zip_path: Optional[str] = None,
    max_files: Optional[int] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Memory-efficient streaming processor for the full 115-file traffic archive (~60M rows).
    
    Streams file-by-file to compute session-aware deltas and aggregates to hourly resolution
    while strictly preserving camera_id and direction.

    Args:
        traffic_zip_path: Optional path to traffic.zip.
        max_files: Optional limit on files to process.

    Returns:
        Tuple of (hourly_traffic_df, audit_metrics).
    """
    import io
    import re
    import zipfile

    search_paths = [
        Path("data/raw/traffic/traffic.zip"),
        Path("data/raw/Heterogeneous Traffic Count Dataset, Pune (Jan 202/traffic.zip"),
    ]
    if traffic_zip_path:
        search_paths.insert(0, Path(traffic_zip_path))

    zip_file = None
    for p in search_paths:
        if p.exists():
            zip_file = p
            break

    if zip_file is None:
        raise FileNotFoundError(f"Traffic archive not found in {[str(p) for p in search_paths]}")

    audit: Dict[str, Any] = {
        "files_processed": 0,
        "raw_rows_processed": 0,
        "total_vehicles_counted": 0.0,
        "active_junctions": [],
        "active_cameras": [],
    }

    hourly_records = []
    junctions = set()
    cameras = set()

    with zipfile.ZipFile(zip_file, "r") as z:
        csv_names = [f for f in sorted(z.namelist()) if f.endswith(".csv")]
        if max_files:
            csv_names = csv_names[:max_files]

        logger.info(f"Streaming and cleaning {len(csv_names)} traffic files from archive...")

        for name in csv_names:
            parts = name.strip("/").split("/")
            if len(parts) < 4:
                continue
            junction, camera_id, filename = parts[1], parts[2], parts[3]
            match = re.search(r"([a-z]\d)_(\d{2})(_one)?\.csv", filename)
            if not match:
                continue

            day = int(match.group(2))
            date_str = f"2023-01-{day:02d}"

            try:
                raw_bytes = z.read(name)
                df = pd.read_csv(io.BytesIO(raw_bytes)).dropna(how="all")
                if df.empty:
                    continue

                audit["raw_rows_processed"] += len(df)
                junctions.add(junction)
                cameras.add(camera_id)

                # Filter valid directions
                valid_dirs = {"UP", "DOWN", "LEFT", "RIGHT"}
                df["Direction"] = df["Direction"].astype(str).str.strip().str.upper()
                df = df[df["Direction"].isin(valid_dirs)]

                # Parse time
                time_series = pd.to_datetime(
                    date_str + " " + df["Time"].astype(str),
                    format="%Y-%m-%d %H:%M:%S",
                    errors="coerce",
                )
                df["timestamp"] = time_series
                df = df.dropna(subset=["timestamp"])

                for c in ["car", "motorbike", "bus", "truck"]:
                    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).clip(lower=0)

                # Session-aware deltas per direction within this file
                df = df.sort_values(["Direction", "timestamp"])
                for c in ["car", "motorbike", "bus", "truck"]:
                    df[f"delta_{c}"] = df.groupby("Direction")[c].diff().fillna(df[c]).clip(lower=0)

                df["traffic_count"] = (
                    df["delta_car"] + df["delta_motorbike"] + df["delta_bus"] + df["delta_truck"]
                )
                audit["total_vehicles_counted"] += float(df["traffic_count"].sum())

                # Aggregate by hour for this camera and direction
                df["timestamp"] = df["timestamp"].dt.floor("1h")
                df["junction"] = junction
                df["camera_id"] = camera_id

                h_agg = df.groupby(
                    ["timestamp", "junction", "camera_id", "Direction"],
                    as_index=False,
                )[["delta_car", "delta_motorbike", "delta_bus", "delta_truck", "traffic_count"]].sum()

                h_agg = h_agg.rename(columns={"Direction": "direction"})
                hourly_records.append(h_agg)
                audit["files_processed"] += 1

            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

    if not hourly_records:
        return pd.DataFrame(), audit

    hourly_df = pd.concat(hourly_records, ignore_index=True)
    # Further group by same hour, junction, camera, direction across continuation files
    hourly_df = hourly_df.groupby(
        ["timestamp", "junction", "camera_id", "direction"],
        as_index=False,
    )[["delta_car", "delta_motorbike", "delta_bus", "delta_truck", "traffic_count"]].sum()

    # Localize to Asia/Kolkata
    hourly_df["timestamp"] = hourly_df["timestamp"].dt.tz_localize(
        "Asia/Kolkata", ambiguous="NaT", nonexistent="shift_forward"
    )

    audit["active_junctions"] = sorted(list(junctions))
    audit["active_cameras"] = sorted(list(cameras))
    audit["hourly_rows"] = len(hourly_df)

    logger.info(
        f"Streaming traffic cleaning complete: {audit['files_processed']} files processed "
        f"({audit['raw_rows_processed']} raw rows). Total vehicles detected: {audit['total_vehicles_counted']:.0f}. "
        f"Produced {audit['hourly_rows']} hourly camera/direction records."
    )
    return hourly_df, audit


# -----------------------------------------------------------------------------
# 2. OPEN-METEO WEATHER CLEANING
# -----------------------------------------------------------------------------
def clean_weather_data(
    raw_weather: Union[Dict[str, Any], str, Path],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw Open-Meteo weather JSON response and verifies physical value ranges.

    Target schema: timestamp, temperature, humidity, wind_speed, rainfall.

    Args:
        raw_weather: Open-Meteo dictionary or path to raw JSON file.

    Returns:
        Tuple of (cleaned_weather_df, audit_metrics_dict).
    """
    audit: Dict[str, Any] = {
        "raw_hours_received": 0,
        "range_violations_corrected": 0,
        "final_valid_hours": 0,
    }

    if isinstance(raw_weather, (str, Path)):
        with open(raw_weather, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif isinstance(raw_weather, dict):
        data = raw_weather
    else:
        raise TypeError(f"Unsupported weather input type: {type(raw_weather)}")

    hourly = data.get("hourly", {})
    if not hourly or "time" not in hourly:
        logger.warning("Empty or invalid weather data structure received.")
        return pd.DataFrame(), audit

    df = pd.DataFrame({
        "time_str": hourly.get("time", []),
        "temperature": hourly.get("temperature_2m", []),
        "humidity": hourly.get("relative_humidity_2m", []),
        "wind_speed": hourly.get("wind_speed_10m", []),
        "rainfall": hourly.get("precipitation", []),
    })

    audit["raw_hours_received"] = len(df)

    # Parse timestamps with explicit timezone
    # Open-Meteo returns 'YYYY-MM-DDTHH:MM' in requested timezone (Asia/Kolkata)
    parsed_time = pd.to_datetime(df["time_str"])
    df["timestamp"] = parsed_time.dt.tz_localize("Asia/Kolkata", ambiguous="NaT", nonexistent="shift_forward")
    df = df.drop(columns=["time_str"])

    # Physical Range Validation
    # Temperature: [-10°C, 60°C]
    temp_invalid = (df["temperature"] < -10) | (df["temperature"] > 60)
    if temp_invalid.any():
        audit["range_violations_corrected"] += int(temp_invalid.sum())
        logger.warning(f"Clipping {temp_invalid.sum()} temperature outliers outside [-10, 60].")
        df["temperature"] = df["temperature"].clip(lower=-10, upper=60)

    # Humidity: [0%, 100%]
    hum_invalid = (df["humidity"] < 0) | (df["humidity"] > 100)
    if hum_invalid.any():
        audit["range_violations_corrected"] += int(hum_invalid.sum())
        logger.warning(f"Clipping {hum_invalid.sum()} humidity outliers outside [0, 100].")
        df["humidity"] = df["humidity"].clip(lower=0, upper=100)

    # Wind speed: >= 0 km/h, <= 200 km/h
    wind_invalid = (df["wind_speed"] < 0) | (df["wind_speed"] > 200)
    if wind_invalid.any():
        audit["range_violations_corrected"] += int(wind_invalid.sum())
        logger.warning(f"Clipping {wind_invalid.sum()} wind speed outliers outside [0, 200].")
        df["wind_speed"] = df["wind_speed"].clip(lower=0, upper=200)

    # Rainfall: >= 0 mm, <= 500 mm
    rain_invalid = (df["rainfall"] < 0) | (df["rainfall"] > 500)
    if rain_invalid.any():
        audit["range_violations_corrected"] += int(rain_invalid.sum())
        logger.warning(f"Clipping {rain_invalid.sum()} rainfall outliers outside [0, 500].")
        df["rainfall"] = df["rainfall"].clip(lower=0, upper=500)

    # Deduplicate and sort by timestamp
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    audit["final_valid_hours"] = len(df)
    audit["time_range_start"] = str(df["timestamp"].min()) if not df.empty else None
    audit["time_range_end"] = str(df["timestamp"].max()) if not df.empty else None

    logger.info(
        f"Weather cleaning complete: {audit['final_valid_hours']} hourly records retained "
        f"from {audit['time_range_start']} to {audit['time_range_end']}."
    )
    return df, audit


# -----------------------------------------------------------------------------
# 3. OPENAQ AIR QUALITY CLEANING
# -----------------------------------------------------------------------------
def clean_air_quality_data(
    raw_measurements: Optional[Union[List[Dict[str, Any]], str, Path]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates and cleans real OpenAQ air quality measurements if available.
    
    If data is absent (e.g. key missing), returns an empty DataFrame with target schema
    and clearly documents that zero real observations are present.

    Args:
        raw_measurements: Optional list of raw measurement dicts or path to JSON file.

    Returns:
        Tuple of (cleaned_aq_df, audit_metrics_dict).
    """
    audit: Dict[str, Any] = {
        "raw_records_received": 0,
        "valid_pm25_records": 0,
        "valid_pm10_records": 0,
        "data_status": "absent",
    }

    if raw_measurements is None:
        # Check standard raw folder for any openaq measurement json files
        aq_dir = Path("data/raw/air_quality")
        json_files = sorted(list(aq_dir.glob("openaq_pune_measurements*.json")))
        records = []
        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        records.extend(content)
            except Exception as e:
                logger.warning(f"Error reading {jf}: {e}")
    elif isinstance(raw_measurements, (str, Path)):
        p = Path(raw_measurements)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                content = json.load(f)
                records = content if isinstance(content, list) else []
        else:
            records = []
    elif isinstance(raw_measurements, list):
        records = raw_measurements
    else:
        records = []

    audit["raw_records_received"] = len(records)

    if not records:
        logger.info(
            "Air quality observations are absent. No real PM2.5/PM10 data available. "
            "Downstream model-ready dataset creation must remain gated."
        )
        empty_df = pd.DataFrame(columns=[
            "timestamp",
            "station_id",
            "station_name",
            "station_lat",
            "station_lon",
            "pm25",
            "pm10",
        ])
        return empty_df, audit

    # Process genuine records
    rows = []
    for r in records:
        val = r.get("value")
        param = r.get("parameter", {}).get("name") if isinstance(r.get("parameter"), dict) else r.get("parameter")
        dt_str = r.get("period", {}).get("datetimeFrom", {}).get("utc") or r.get("datetime")
        coords = r.get("coordinates", {})

        if val is None or val < 0 or val > 1500:  # Physical plausibility bound
            continue

        rows.append({
            "datetime_utc": dt_str,
            "station_id": r.get("location_id"),
            "station_name": r.get("location_name"),
            "station_lat": coords.get("latitude"),
            "station_lon": coords.get("longitude"),
            "parameter": param,
            "value": float(val),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), audit

    # Parse timestamps and localize to Asia/Kolkata
    df["timestamp"] = pd.to_datetime(df["datetime_utc"]).dt.tz_convert("Asia/Kolkata")
    
    # Pivot parameters into pm25 and pm10 columns
    pivoted = df.pivot_table(
        index=["timestamp", "station_id", "station_name", "station_lat", "station_lon"],
        columns="parameter",
        values="value",
        aggfunc="mean",
    ).reset_index()

    pivoted = pivoted.rename(columns={"pm25": "pm25", "pm10": "pm10"})
    if "pm25" not in pivoted.columns:
        pivoted["pm25"] = np.nan
    if "pm10" not in pivoted.columns:
        pivoted["pm10"] = np.nan

    audit["valid_pm25_records"] = int(pivoted["pm25"].notna().sum())
    audit["valid_pm10_records"] = int(pivoted["pm10"].notna().sum())
    audit["data_status"] = "present"

    logger.info(
        f"Air quality cleaning complete: {len(pivoted)} records. "
        f"PM2.5 non-null: {audit['valid_pm25_records']}, PM10 non-null: {audit['valid_pm10_records']}."
    )
    return pivoted, audit
