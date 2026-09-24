"""
AERIS Data Cleaning & Validation Module (ml/src/clean.py)
=========================================================
Implements canonical, auditable data cleaning for:
1. Heterogeneous Traffic Dataset (session-aware counter processing)
2. Open-Meteo Weather observations
3. OpenAQ Air Quality observations

Strict Rules Enforced:
- ZERO FABRICATION: Missing measurement values are NEVER imputed as zeros.
- NO CLIPPING: Out-of-range observations are flagged/excluded, not silently replaced.
- CANONICAL LOGIC: Streaming and non-streaming traffic cleaning share identical session logic.
- FIRST-ROW BASELINE: First row of each session establishes baseline (delta = 0).
- TIMEZONE CONSISTENCY: All output timestamps are timezone-aware Asia/Kolkata.
"""

import io
import json
import logging
import re
import zipfile
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

COUNT_COLUMNS = ["car", "motorbike", "bus", "truck"]
VALID_DIRECTIONS = {"UP", "DOWN", "LEFT", "RIGHT"}


# -----------------------------------------------------------------------------
# 1. CANONICAL TRAFFIC SESSION CLEANING
# -----------------------------------------------------------------------------
def clean_traffic_session(
    session_df: pd.DataFrame,
    session_file: Optional[str] = None,
    junction: Optional[str] = None,
    camera_id: Optional[str] = None,
    date_str: Optional[str] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Canonical cleaning logic for a single traffic recording session.

    Policy on Missing Measurements:
    - Never uses fillna(0) on raw vehicle counts. Missing values are NOT zero vehicles.
    - Rows with missing or non-numeric count measurements are excluded prior to delta
      computation so they cannot cause artificial positive spikes.
    - First observation in a session for each direction establishes the initial baseline
      (delta = 0.0), so arbitrary starting counts do not fabricate vehicles.
    - If a continuation file (_one.csv) occurs, it is treated as a separate session boundary.

    Args:
        session_df: DataFrame containing raw rows from one session.
        session_file: Optional session filename for traceability.
        junction: Optional junction name.
        camera_id: Optional camera identifier.
        date_str: Optional date string (YYYY-MM-DD).

    Returns:
        Tuple of (cleaned_session_df, audit_metrics_dict).
    """
    audit: Dict[str, Any] = {
        "session_file": session_file,
        "initial_rows": len(session_df),
        "dropped_all_null_rows": 0,
        "missing_timestamp_rows": 0,
        "invalid_direction_rows": 0,
        "missing_measurement_rows": 0,
        "invalid_negative_count_rows": 0,
        "final_valid_rows": 0,
        "total_vehicles_counted": 0.0,
    }

    if session_df.empty:
        return pd.DataFrame(), audit

    df = session_df.copy()

    # Metadata resolution
    s_file = session_file or (df["session_file"].iloc[0] if "session_file" in df.columns else "unknown_session")
    junc = junction or (df["junction"].iloc[0] if "junction" in df.columns else "unknown_junction")
    cam = camera_id or (df["camera_id"].iloc[0] if "camera_id" in df.columns else "unknown_camera")
    d_str = date_str or (df["date"].iloc[0] if "date" in df.columns else None)

    # 1. Drop completely empty rows
    req_cols = [c for c in ["Time", "Direction"] + COUNT_COLUMNS if c in df.columns]
    before_all_null = len(df)
    df = df.dropna(subset=req_cols, how="all")
    audit["dropped_all_null_rows"] = before_all_null - len(df)

    if df.empty:
        return pd.DataFrame(), audit

    # 2. Validate and standardize Direction
    if "Direction" not in df.columns:
        logger.warning(f"Session {s_file} missing 'Direction' column.")
        return pd.DataFrame(), audit

    df["Direction"] = df["Direction"].astype(str).str.strip().str.upper()
    valid_dir_mask = df["Direction"].isin(VALID_DIRECTIONS)
    audit["invalid_direction_rows"] = int((~valid_dir_mask).sum())
    df = df[valid_dir_mask]

    if df.empty:
        return pd.DataFrame(), audit

    # 3. Detect and exclude missing vehicle count measurements (NO fillna(0))
    for c in COUNT_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
        else:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Detect rows where ANY count column is NaN (missing measurement)
    missing_measurements_mask = df[COUNT_COLUMNS].isna().any(axis=1)
    audit["missing_measurement_rows"] = int(missing_measurements_mask.sum())
    if audit["missing_measurement_rows"] > 0:
        logger.warning(
            f"Session {s_file}: Excluding {audit['missing_measurement_rows']} rows with missing "
            "vehicle count measurements to prevent artificial delta fabrication."
        )
        df = df[~missing_measurements_mask]

    if df.empty:
        return pd.DataFrame(), audit

    # Detect rows with negative vehicle counts (physically impossible)
    negative_counts_mask = (df[COUNT_COLUMNS] < 0).any(axis=1)
    audit["invalid_negative_count_rows"] = int(negative_counts_mask.sum())
    if audit["invalid_negative_count_rows"] > 0:
        logger.warning(
            f"Session {s_file}: Excluding {audit['invalid_negative_count_rows']} rows with negative "
            "vehicle count values."
        )
        df = df[~negative_counts_mask]

    if df.empty:
        return pd.DataFrame(), audit

    # 4. Parse Timestamps with explicit timezone (Asia/Kolkata)
    if "Time" not in df.columns:
        logger.warning(f"Session {s_file} missing 'Time' column.")
        return pd.DataFrame(), audit

    if d_str is None:
        # Fallback date extraction from session_file name if available
        match = re.search(r"_(\d{2})(_one)?\.csv", s_file)
        if match:
            d_str = f"2023-01-{int(match.group(1)):02d}"
        else:
            d_str = "2023-01-01"

    datetime_str = d_str + " " + df["Time"].astype(str)
    parsed_timestamps = pd.to_datetime(datetime_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    invalid_time_mask = parsed_timestamps.isna()
    audit["missing_timestamp_rows"] = int(invalid_time_mask.sum())
    df = df[~invalid_time_mask]
    parsed_timestamps = parsed_timestamps[~invalid_time_mask]

    if df.empty:
        return pd.DataFrame(), audit

    df["timestamp"] = parsed_timestamps.dt.tz_localize(
        "Asia/Kolkata", ambiguous="NaT", nonexistent="shift_forward"
    )

    # 5. Deterministic sorting for chronological delta computation preserving source row order
    if "_source_row" not in df.columns:
        df["_source_row"] = np.arange(len(df))

    df = df.sort_values(["Direction", "timestamp", "_source_row"]).reset_index(drop=True)

    # 6. Session-aware delta computation with First-Row Baseline
    # Group strictly by Direction within this single session file
    for c in COUNT_COLUMNS:
        delta_col = f"delta_{c}"
        # diff() leaves NaN at the first row of each direction in the session.
        # First row establishes the initial counter baseline: delta = 0.0.
        # Clipping at 0 ensures any internal sensor anomalies cannot produce negative deltas.
        df[delta_col] = df.groupby("Direction")[c].diff().fillna(0.0).clip(lower=0.0)

    # Calculate total traffic delta for this observation
    df["traffic_count"] = (
        df["delta_car"] + df["delta_motorbike"] + df["delta_bus"] + df["delta_truck"]
    )

    # Traceable standardized output schema
    df["junction"] = junc
    df["camera_id"] = cam
    df["session_file"] = s_file
    df["direction"] = df["Direction"]

    cols_to_keep = [
        "timestamp",
        "junction",
        "camera_id",
        "direction",
        "session_file",
        "_source_row",
        "car",
        "motorbike",
        "bus",
        "truck",
        "delta_car",
        "delta_motorbike",
        "delta_bus",
        "delta_truck",
        "traffic_count",
    ]
    cols_to_keep = [c for c in cols_to_keep if c in df.columns]

    cleaned_df = df[cols_to_keep].rename(columns={
        "car": "car_raw",
        "motorbike": "motorbike_raw",
        "bus": "bus_raw",
        "truck": "truck_raw",
    })

    audit["final_valid_rows"] = len(cleaned_df)
    audit["total_vehicles_counted"] = float(cleaned_df["traffic_count"].sum())

    return cleaned_df, audit


# -----------------------------------------------------------------------------
# 2. MULTI-SESSION TRAFFIC CLEANING (NON-STREAMING)
# -----------------------------------------------------------------------------
def clean_traffic_data(
    raw_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw traffic observations across multiple sessions using canonical session logic.
    Guarantees equivalence with clean_traffic_stream on identical inputs.

    Args:
        raw_df: Raw traffic DataFrame from ingest_traffic().

    Returns:
        Tuple of (cleaned_df, combined_audit_dict).
    """
    overall_audit: Dict[str, Any] = {
        "initial_rows": len(raw_df),
        "dropped_all_null_rows": 0,
        "missing_timestamp_rows": 0,
        "invalid_direction_rows": 0,
        "missing_measurement_rows": 0,
        "invalid_negative_count_rows": 0,
        "final_valid_rows": 0,
        "total_vehicles_counted": 0.0,
        "active_junctions": [],
        "active_cameras": [],
    }

    if raw_df.empty:
        logger.warning("Empty DataFrame passed to clean_traffic_data.")
        return pd.DataFrame(), overall_audit

    df = raw_df.copy()
    if "session_file" not in df.columns:
        df["session_file"] = "default_session.csv"
    if "junction" not in df.columns:
        df["junction"] = "default_junction"
    if "camera_id" not in df.columns:
        df["camera_id"] = "default_camera"
    if "_source_row" not in df.columns:
        df["_source_row"] = df.groupby(["junction", "camera_id", "session_file"]).cumcount()

    cleaned_session_list = []
    # Group strictly by session boundaries: junction, camera_id, session_file
    session_groups = df.groupby(["junction", "camera_id", "session_file"], as_index=False)

    for (junc, cam, s_file), group_data in session_groups:
        s_clean, s_audit = clean_traffic_session(
            session_df=group_data,
            session_file=s_file,
            junction=junc,
            camera_id=cam,
        )
        if not s_clean.empty:
            cleaned_session_list.append(s_clean)

        overall_audit["dropped_all_null_rows"] += s_audit["dropped_all_null_rows"]
        overall_audit["missing_timestamp_rows"] += s_audit["missing_timestamp_rows"]
        overall_audit["invalid_direction_rows"] += s_audit["invalid_direction_rows"]
        overall_audit["missing_measurement_rows"] += s_audit["missing_measurement_rows"]
        overall_audit["invalid_negative_count_rows"] += s_audit["invalid_negative_count_rows"]
        overall_audit["total_vehicles_counted"] += s_audit["total_vehicles_counted"]

    if not cleaned_session_list:
        return pd.DataFrame(), overall_audit

    total_cleaned_df = pd.concat(cleaned_session_list, ignore_index=True)
    overall_audit["final_valid_rows"] = len(total_cleaned_df)
    overall_audit["active_junctions"] = sorted(total_cleaned_df["junction"].unique().tolist())
    overall_audit["active_cameras"] = sorted(total_cleaned_df["camera_id"].unique().tolist())

    logger.info(
        f"Non-streaming traffic cleaning complete: {overall_audit['final_valid_rows']} valid rows retained from "
        f"{overall_audit['initial_rows']} initial rows. Total vehicles detected: {overall_audit['total_vehicles_counted']:.0f}."
    )
    return total_cleaned_df, overall_audit


# -----------------------------------------------------------------------------
# 3. STREAMING TRAFFIC CLEANING
# -----------------------------------------------------------------------------
def clean_traffic_stream(
    traffic_zip_path: Optional[str] = None,
    max_files: Optional[int] = None,
    aggregate_hourly: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Memory-efficient streaming processor for the full 115-file traffic archive.
    Uses canonical clean_traffic_session() per file to guarantee equivalent logic.

    Args:
        traffic_zip_path: Optional path to traffic.zip.
        max_files: Optional limit on files to process.
        aggregate_hourly: If True, aggregates to hourly resolution. If False, returns raw cleaned rows.

    Returns:
        Tuple of (cleaned_df, audit_metrics).
    """
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

    overall_audit: Dict[str, Any] = {
        "files_processed": 0,
        "raw_rows_processed": 0,
        "dropped_all_null_rows": 0,
        "missing_timestamp_rows": 0,
        "invalid_direction_rows": 0,
        "missing_measurement_rows": 0,
        "invalid_negative_count_rows": 0,
        "final_valid_rows": 0,
        "total_vehicles_counted": 0.0,
        "active_junctions": [],
        "active_cameras": [],
    }

    accumulated_records = []
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
            junc, cam, filename = parts[1], parts[2], parts[3]
            match = re.search(r"([a-z]\d)_(\d{2})(_one)?\.csv", filename)
            if not match:
                continue

            day = int(match.group(2))
            date_str = f"2023-01-{day:02d}"

            try:
                raw_bytes = z.read(name)
                raw_file_df = pd.read_csv(io.BytesIO(raw_bytes))
                raw_file_df["_source_row"] = np.arange(len(raw_file_df))
                overall_audit["raw_rows_processed"] += len(raw_file_df)

                # Invoke canonical session cleaning
                s_clean, s_audit = clean_traffic_session(
                    session_df=raw_file_df,
                    session_file=filename,
                    junction=junc,
                    camera_id=cam,
                    date_str=date_str,
                )

                overall_audit["dropped_all_null_rows"] += s_audit["dropped_all_null_rows"]
                overall_audit["missing_timestamp_rows"] += s_audit["missing_timestamp_rows"]
                overall_audit["invalid_direction_rows"] += s_audit["invalid_direction_rows"]
                overall_audit["missing_measurement_rows"] += s_audit["missing_measurement_rows"]
                overall_audit["invalid_negative_count_rows"] += s_audit["invalid_negative_count_rows"]
                overall_audit["total_vehicles_counted"] += s_audit["total_vehicles_counted"]
                overall_audit["files_processed"] += 1

                if s_clean.empty:
                    continue

                junctions.add(junc)
                cameras.add(cam)

                if aggregate_hourly:
                    # Hourly aggregation step
                    s_clean["timestamp"] = s_clean["timestamp"].dt.floor("1h")
                    h_agg = s_clean.groupby(
                        ["timestamp", "junction", "camera_id", "direction"],
                        as_index=False,
                    )[["delta_car", "delta_motorbike", "delta_bus", "delta_truck", "traffic_count"]].sum()
                    accumulated_records.append(h_agg)
                else:
                    accumulated_records.append(s_clean)

            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

    if not accumulated_records:
        return pd.DataFrame(), overall_audit

    res_df = pd.concat(accumulated_records, ignore_index=True)

    if aggregate_hourly:
        # Consolidate continuation files covering same hour
        res_df = res_df.groupby(
            ["timestamp", "junction", "camera_id", "direction"],
            as_index=False,
        )[["delta_car", "delta_motorbike", "delta_bus", "delta_truck", "traffic_count"]].sum()

    overall_audit["final_valid_rows"] = len(res_df)
    overall_audit["active_junctions"] = sorted(list(junctions))
    overall_audit["active_cameras"] = sorted(list(cameras))

    logger.info(
        f"Streaming traffic cleaning complete: {overall_audit['files_processed']} files processed. "
        f"Produced {overall_audit['final_valid_rows']} {'hourly' if aggregate_hourly else 'row'} records. "
        f"Total vehicles: {overall_audit['total_vehicles_counted']:.0f}."
    )
    return res_df, overall_audit


# -----------------------------------------------------------------------------
# 4. OPEN-METEO WEATHER CLEANING
# -----------------------------------------------------------------------------
def clean_weather_data(
    raw_weather: Union[Dict[str, Any], str, Path],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw Open-Meteo weather JSON response.
    
    Zero-Fabrication Policy:
    - Never clips out-of-range observations to make them appear valid.
    - Physical bounds violations are flagged, audited, and excluded from model-ready data.
    - All timestamps are preserved with timezone Asia/Kolkata.

    Args:
        raw_weather: Open-Meteo dictionary or path to raw JSON file.

    Returns:
        Tuple of (cleaned_weather_df, audit_metrics_dict).
    """
    audit: Dict[str, Any] = {
        "raw_hours_received": 0,
        "invalid_temperature_count": 0,
        "invalid_humidity_count": 0,
        "invalid_wind_speed_count": 0,
        "invalid_rainfall_count": 0,
        "total_invalid_hours_excluded": 0,
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
    if df.empty:
        return pd.DataFrame(), audit

    # 1. Parse timestamps with explicit timezone (Asia/Kolkata)
    parsed_time = pd.to_datetime(df["time_str"], errors="coerce")
    invalid_time_mask = parsed_time.isna()
    df = df[~invalid_time_mask].copy()
    parsed_time = parsed_time[~invalid_time_mask]
    df["timestamp"] = parsed_time.dt.tz_localize(
        "Asia/Kolkata", ambiguous="NaT", nonexistent="shift_forward"
    )
    df = df.drop(columns=["time_str"])

    # 2. Strict Physical Range Validation (NO CLIPPING)
    # Convert all metrics to numeric
    for col in ["temperature", "humidity", "wind_speed", "rainfall"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Physical bounds checks:
    # Temperature: [-10°C, 60°C]
    invalid_temp = (df["temperature"] < -10) | (df["temperature"] > 60) | df["temperature"].isna()
    # Humidity: [0%, 100%]
    invalid_hum = (df["humidity"] < 0) | (df["humidity"] > 100) | df["humidity"].isna()
    # Wind speed: [0 km/h, 200 km/h]
    invalid_wind = (df["wind_speed"] < 0) | (df["wind_speed"] > 200) | df["wind_speed"].isna()
    # Rainfall: [0 mm, 500 mm]
    invalid_rain = (df["rainfall"] < 0) | (df["rainfall"] > 500) | df["rainfall"].isna()

    audit["invalid_temperature_count"] = int(invalid_temp.sum())
    audit["invalid_humidity_count"] = int(invalid_hum.sum())
    audit["invalid_wind_speed_count"] = int(invalid_wind.sum())
    audit["invalid_rainfall_count"] = int(invalid_rain.sum())

    invalid_any_mask = invalid_temp | invalid_hum | invalid_wind | invalid_rain
    audit["total_invalid_hours_excluded"] = int(invalid_any_mask.sum())

    if audit["total_invalid_hours_excluded"] > 0:
        logger.warning(
            f"Excluding {audit['total_invalid_hours_excluded']} weather records failing physical bounds "
            f"(temp: {audit['invalid_temperature_count']}, hum: {audit['invalid_humidity_count']}, "
            f"wind: {audit['invalid_wind_speed_count']}, rain: {audit['invalid_rainfall_count']}). "
            "Replacement values are strictly not fabricated."
        )
        df = df[~invalid_any_mask].copy()

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
# 5. OPENAQ AIR QUALITY CLEANING
# -----------------------------------------------------------------------------
def clean_air_quality_data(
    raw_measurements: Optional[Union[List[Dict[str, Any]], str, Path]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates and cleans real OpenAQ air quality measurements if available.
    
    Timestamps are parsed as UTC and converted to Asia/Kolkata.
    Zero imputation or synthetic replacement is performed.

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
        aq_dir = Path("data/raw/air_quality")
        json_files = sorted(list(aq_dir.glob("*pune_measurements*.json")))
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

    rows = []
    for r in records:
        val = r.get("value")
        raw_param = (
            r.get("parameter", {}).get("name")
            if isinstance(r.get("parameter"), dict)
            else (r.get("parameter") or r.get("parameter_name"))
        )
        if not raw_param:
            continue
        param_norm = str(raw_param).lower().replace(".", "").replace("-", "").strip()
        if param_norm not in ["pm25", "pm10"]:
            continue

        dt_str = (
            r.get("collected_at")
            or (r.get("period", {}).get("datetimeFrom", {}).get("utc") if isinstance(r.get("period"), dict) else None)
            or r.get("datetime_utc")
            or r.get("datetime")
        )
        if not dt_str:
            continue

        coords = r.get("coordinates") or {}
        lat = r.get("station_lat") or (coords.get("latitude") if isinstance(coords, dict) else None)
        lon = r.get("station_lon") or (coords.get("longitude") if isinstance(coords, dict) else None)
        station_id = r.get("station_id") or r.get("location_id")
        station_name = r.get("station_name") or r.get("location_name")

        # Guard against misattributed stations in upstream registries
        if "moradabad" in str(station_name).lower() or "uppcb" in str(station_name).lower():
            continue

        if val is None:
            continue
        try:
            val_float = float(val)
        except (ValueError, TypeError):
            continue

        # Physical plausibility bound: [0, 1500] ug/m3
        if val_float < 0 or val_float > 1500:
            continue

        rows.append({
            "datetime_raw": dt_str,
            "station_id": station_id,
            "station_name": station_name,
            "station_lat": lat,
            "station_lon": lon,
            "parameter": param_norm,
            "value": val_float,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), audit

    # Parse timestamps and enforce Asia/Kolkata
    parsed_dt = pd.to_datetime(df["datetime_raw"], errors="coerce")
    valid_dt_mask = parsed_dt.notna()
    df = df[valid_dt_mask].copy()
    parsed_dt = parsed_dt[valid_dt_mask]

    # Convert or localize to Asia/Kolkata
    if parsed_dt.dt.tz is None:
        df["timestamp"] = parsed_dt.dt.tz_localize("Asia/Kolkata", ambiguous="NaT", nonexistent="shift_forward")
    else:
        df["timestamp"] = parsed_dt.dt.tz_convert("Asia/Kolkata")

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
    audit["data_status"] = "present" if audit["valid_pm25_records"] > 0 else "absent"

    logger.info(
        f"Air quality cleaning complete: {len(pivoted)} records. "
        f"PM2.5 non-null: {audit['valid_pm25_records']}, PM10 non-null: {audit['valid_pm10_records']}."
    )
    return pivoted, audit
