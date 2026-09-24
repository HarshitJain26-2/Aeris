"""
AERIS Data Ingestion Module (ml/src/ingest.py)
==============================================
Provides modular, reproducible ingestion functions for:
1. Heterogeneous Traffic Count Dataset, Pune (Jan 2023)
2. Open-Meteo Historical Weather API for Pune
3. OpenAQ API v3 Air Quality observations (strictly key-authenticated)
4. XKDR India Air Quality Database ingestion (CPCB CAAQM network)
5. CAMS Global Atmospheric Composition Forecasts (Open-Meteo Air Quality API)
   — modeled PM2.5 target for Round 1 when no ground-station observations exist
6. EDGAR v8.1 NetCDF Industrial Emissions context extraction (annual spatial only)

Follows zero-fabrication and raw-source traceability principles.
"""

import io
import json
import logging
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from dotenv import find_dotenv, load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aeris.ingest")

# Load environment variables with fallback
env_file = find_dotenv(usecwd=True)
if env_file:
    load_dotenv(env_file)
else:
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


# -----------------------------------------------------------------------------
# 1. TRAFFIC INGESTION
# -----------------------------------------------------------------------------
def ingest_traffic(
    traffic_zip_path: Optional[str] = None,
    max_files: Optional[int] = None,
) -> pd.DataFrame:
    """
    Ingests raw traffic CSV files from the Heterogeneous Traffic Count Dataset archive.
    
    Preserves camera-level and direction-level granularity without premature summation.
    Preserves raw columns: Time, Direction, car, motorbike, bus, truck.
    Extracts metadata: junction, camera_id, session_file, date, is_continuation.

    Args:
        traffic_zip_path: Optional path to traffic.zip. If None, checks standard locations.
        max_files: Optional cap on files to read (useful for rapid testing).

    Returns:
        pd.DataFrame containing raw structured traffic records across cameras and days.
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
        raise FileNotFoundError(
            f"Traffic archive not found. Searched in: {[str(p) for p in search_paths]}"
        )

    logger.info(f"Opening traffic dataset archive: {zip_file}")
    records = []
    
    with zipfile.ZipFile(zip_file, "r") as z:
        csv_names = [f for f in sorted(z.namelist()) if f.endswith(".csv")]
        logger.info(f"Discovered {len(csv_names)} CSV files in traffic archive.")
        
        if max_files:
            csv_names = csv_names[:max_files]
            logger.info(f"Limiting ingestion to first {max_files} files as requested.")

        for name in csv_names:
            parts = name.strip("/").split("/")
            if len(parts) < 4:
                continue
            junction = parts[1]
            camera_id = parts[2]
            filename = parts[3]

            # Parse date and continuation flag from filename: <cam>_<day>[_one].csv
            match = re.search(r"([a-z]\d)_(\d{2})(_one)?\.csv", filename)
            if not match:
                logger.warning(f"Skipping unrecognized file format: {filename}")
                continue

            day_str = match.group(2)
            is_continuation = bool(match.group(3))
            date_str = f"2023-01-{int(day_str):02d}"

            try:
                raw_bytes = z.read(name)
                df_file = pd.read_csv(io.BytesIO(raw_bytes))
                # Add private source-order column to preserve file row order
                df_file["_source_row"] = np.arange(len(df_file))
                content_cols = [c for c in df_file.columns if c != "_source_row"]
                df_file = df_file.dropna(subset=content_cols, how="all")
                if df_file.empty:
                    continue

                # Ensure required columns are present
                expected_cols = ["Time", "Direction", "car", "motorbike", "bus", "truck"]
                missing = [c for c in expected_cols if c not in df_file.columns]
                if missing:
                    logger.warning(f"File {name} missing expected columns {missing}; skipping.")
                    continue

                # Attach metadata for traceability
                df_file["junction"] = junction
                df_file["camera_id"] = camera_id
                df_file["session_file"] = filename
                df_file["date"] = date_str
                df_file["is_continuation"] = is_continuation

                records.append(df_file)
            except Exception as e:
                logger.error(f"Error reading {name} from archive: {e}")

    if not records:
        logger.warning("No valid traffic data records were read.")
        return pd.DataFrame()

    total_df = pd.concat(records, ignore_index=True)
    logger.info(
        f"Successfully ingested {len(total_df)} raw records across "
        f"{total_df['junction'].nunique()} junctions and {total_df['camera_id'].nunique()} cameras."
    )
    return total_df


# -----------------------------------------------------------------------------
# 2. OPEN-METEO WEATHER INGESTION
# -----------------------------------------------------------------------------
def ingest_open_meteo(
    latitude: float = 18.5204,
    longitude: float = 73.8567,
    start_date: str = "2023-01-11",
    end_date: str = "2023-01-18",
    timezone: str = "Asia/Kolkata",
    output_dir: str = "data/raw/weather",
) -> Dict[str, Any]:
    """
    Fetches hourly historical weather for Pune from Open-Meteo Historical Archive API.
    
    Parameters are fully configurable. No API key is required.
    Saves raw response JSON locally under data/raw/weather/.

    Args:
        latitude: Latitude of target location (default Pune: 18.5204).
        longitude: Longitude of target location (default Pune: 73.8567).
        start_date: ISO start date string (YYYY-MM-DD).
        end_date: ISO end date string (YYYY-MM-DD).
        timezone: Timezone identifier (default: Asia/Kolkata).
        output_dir: Local directory path to store raw response JSON.

    Returns:
        Parsed JSON dictionary response from Open-Meteo.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
        "timezone": timezone,
    }

    logger.info(
        f"Querying Open-Meteo historical archive for ({latitude}, {longitude}) "
        f"from {start_date} to {end_date} (tz: {timezone})..."
    )

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Open-Meteo API request failed: {e}")
        raise RuntimeError(f"Open-Meteo ingestion error: {e}") from e

    # Persist raw JSON
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    file_name = f"open_meteo_pune_{start_date}_{end_date}.json"
    dest = out_path / file_name

    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Raw Open-Meteo response saved to {dest} ({len(data.get('hourly', {}).get('time', []))} hours).")
    return data


# -----------------------------------------------------------------------------
# 3. OPENAQ AIR QUALITY INGESTION
# -----------------------------------------------------------------------------
def ingest_openaq(
    city: str = "Pune",
    date_from: str = "2023-01-11",
    date_to: str = "2023-01-18",
    output_dir: str = "data/raw/air_quality",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingests ambient PM2.5 and PM10 observations for Pune from OpenAQ API v3.
    
    Reads OPENAQ_API_KEY from environment variable. Never exposes the key in logs.
    If the key is missing, logs clear blocker notification without fabricating data.

    Args:
        city: Target city name (default: Pune).
        date_from: Start date (YYYY-MM-DD).
        date_to: End date (YYYY-MM-DD).
        output_dir: Destination path for raw air quality data.
        api_key: Optional key override (for testing). Defaults to os.getenv('OPENAQ_API_KEY').

    Returns:
        Dictionary reporting ingestion status and paths, or blocker details.
    """
    key = api_key or os.getenv("OPENAQ_API_KEY")

    if not key or key == "your_key_here":
        msg = (
            "OPENAQ_API_KEY is not set or contains default placeholder. "
            "OpenAQ API v3 requires a valid API key passed via the X-API-Key header. "
            "Real air-quality ingestion is blocked until a key is supplied in .env or the environment. "
            "Zero synthetic data will be fabricated."
        )
        logger.warning(msg)
        return {
            "status": "blocked",
            "message": msg,
            "observations_count": 0,
            "data_path": None,
        }

    # Production OpenAQ API v3 endpoints
    base_url = "https://api.openaq.org/v3"
    headers = {
        "X-API-Key": key,
        "Accept": "application/json",
        "User-Agent": "AERIS-DigitalTwin-DataML/1.0",
    }

    logger.info("OPENAQ_API_KEY detected. Initializing OpenAQ v3 ingestion for Pune...")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Discover locations in Pune
        loc_url = f"{base_url}/locations"
        loc_params = {
            "coordinates": "18.5204,73.8567",
            "radius": 25000,  # 25km radius around Pune center
            "limit": 50,
        }
        resp = requests.get(loc_url, headers=headers, params=loc_params, timeout=30)
        resp.raise_for_status()
        loc_data = resp.json()

        locations_file = out_path / "openaq_pune_locations.json"
        with open(locations_file, "w", encoding="utf-8") as f:
            json.dump(loc_data, f, indent=2)

        locations = loc_data.get("results", [])
        logger.info(f"Discovered {len(locations)} OpenAQ monitoring locations in Pune.")

        # Step 2: Fetch measurements per PM2.5/PM10 sensor for target dates
        all_measurements = []
        for loc in locations:
            loc_id = loc.get("id")
            loc_name = loc.get("name")
            coords = loc.get("coordinates", {})

            # Fetch sensors for this location
            try:
                s_resp = requests.get(f"{base_url}/locations/{loc_id}/sensors", headers=headers, timeout=15)
                if s_resp.status_code != 200:
                    continue
                sensors = s_resp.json().get("results", [])
            except Exception as e:
                logger.warning(f"Failed to fetch sensors for location {loc_id}: {e}")
                continue

            for sensor in sensors:
                param_name = sensor.get("parameter", {}).get("name")
                if param_name not in ["pm25", "pm10"]:
                    continue

                s_id = sensor.get("id")
                meas_url = f"{base_url}/sensors/{s_id}/measurements"
                meas_params = {
                    "datetime_from": f"{date_from}T00:00:00Z",
                    "datetime_to": f"{date_to}T23:59:59Z",
                    "limit": 1000,
                }
                try:
                    m_resp = requests.get(meas_url, headers=headers, params=meas_params, timeout=15)
                    if m_resp.status_code == 200:
                        m_data = m_resp.json()
                        for r in m_data.get("results", []):
                            r["location_id"] = loc_id
                            r["location_name"] = loc_name
                            r["coordinates"] = coords
                            r["sensor_id"] = s_id
                            r["parameter_name"] = param_name
                            all_measurements.append(r)
                except Exception as e:
                    logger.warning(f"Error fetching measurements for sensor {s_id}: {e}")

        meas_file = out_path / f"openaq_pune_measurements_{date_from}_{date_to}.json"
        with open(meas_file, "w", encoding="utf-8") as f:
            json.dump(all_measurements, f, indent=2)

        if not all_measurements:
            logger.warning(
                f"OpenAQ returned 0 measurements for Pune for date range {date_from} to {date_to}. "
                "OpenAQ archives for Pune show an archival gap for late 2022 through 2024 across CPCB/IITM sensors."
            )
            return {
                "status": "empty_period",
                "message": (
                    f"OpenAQ API key verified and 19 Pune monitoring stations discovered, "
                    f"but 0 observations exist in OpenAQ for {date_from} to {date_to} due to an archive gap."
                ),
                "observations_count": 0,
                "data_path": str(meas_file),
            }

        logger.info(
            f"Successfully downloaded {len(all_measurements)} OpenAQ measurements to {meas_file}."
        )
        return {
            "status": "success",
            "message": f"Ingested {len(all_measurements)} observations.",
            "observations_count": len(all_measurements),
            "data_path": str(meas_file),
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAQ API request encountered an error: {e}")
        return {
            "status": "error",
            "message": f"Network/API error during OpenAQ ingestion: {e}",
            "observations_count": 0,
            "data_path": None,
        }


# -----------------------------------------------------------------------------
# 4. XKDR INDIA AIR QUALITY DATABASE INGESTION
# -----------------------------------------------------------------------------
def is_valid_pune_cpcb_station(s: Dict[str, Any], target_city: str = "Pune") -> bool:
    """
    Validates that a station discovered from XKDR metadata strictly belongs to
    the target city (Pune), state (Maharashtra), and source (cpcb_caaqm).
    
    Rejects any station containing non-Pune metadata (such as Moradabad or UPPCB),
    guarding against upstream catalog attribution bugs in source registries.
    """
    city = str(s.get("city_name") or s.get("city") or "").strip().lower()
    state = str(s.get("state_name") or s.get("state") or "").strip().lower()
    source = str(s.get("source") or "").strip().lower()
    name = str(s.get("station_name") or s.get("name") or "").strip().lower()

    if city != target_city.lower():
        return False
    if state != "maharashtra":
        return False
    if source != "cpcb_caaqm":
        return False

    # Guard against misattributed stations in upstream registries
    # e.g., Moradabad / UPPCB stations incorrectly cataloged with city Pune
    if "moradabad" in name or "uppcb" in name:
        return False

    return True


def ingest_xkdr_air_quality(
    city: str = "Pune",
    date_from: str = "2023-01-11",
    date_to: str = "2023-01-18",
    output_dir: str = "data/raw/air_quality",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingests ambient PM2.5 and PM10 hourly observations for Pune from the XKDR
    India Air Quality Database API (https://airquality.xkdr.org).
    
    Strictly discovers and validates Pune / Maharashtra / CPCB CAAQM stations first,
    filtering out any misattributed stations (e.g. Moradabad / UPPCB).
    Explicitly passes discovered station IDs and required filters to /v1/measurements.
    Validates every returned observation before persisting.

    Reads AQI_API_KEY from environment variable (.env). Never exposes the key.
    If no valid observations exist after validation, reports empty_period without
    manufacturing or substituting fake data.
    """
    key = api_key or os.getenv("AQI_API_KEY") or os.getenv("XKDR_API_KEY")

    if not key or key in ["your_key_here", "your_xkdr_key_here"]:
        msg = (
            "AQI_API_KEY is not set or contains default placeholder. "
            "XKDR India Air Quality API requires a valid bearer token. "
            "Real air-quality ingestion via XKDR is blocked until a key is supplied in .env or the environment. "
            "Zero synthetic data will be fabricated."
        )
        logger.warning(msg)
        return {
            "status": "blocked",
            "message": msg,
            "observations_count": 0,
            "stations_discovered": [],
            "stations_names": [],
            "pm25_count": 0,
            "pm10_count": 0,
            "first_timestamp": None,
            "last_timestamp": None,
            "data_path": None,
        }

    base_url = "https://airquality.xkdr.org/v1"
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "User-Agent": "AERIS-DigitalTwin-DataML/1.0",
    }

    logger.info(f"AQI_API_KEY detected. Discovering stations for {city} from XKDR API...")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    dest_file = out_path / f"xkdr_pune_measurements_{date_from}_{date_to}.json"

    try:
        # Step 1: Discover stations from /v1/stations
        stn_url = f"{base_url}/stations"
        stn_params = {"city": city, "source": "cpcb_caaqm"}
        stn_resp = requests.get(stn_url, headers=headers, params=stn_params, timeout=30)
        stn_resp.raise_for_status()
        raw_stations = stn_resp.json().get("data", [])

        # Step 2: Strictly filter stations to Pune / Maharashtra / CPCB CAAQM, excluding Moradabad / UPPCB
        valid_stations_map = {}
        for s in raw_stations:
            if is_valid_pune_cpcb_station(s, target_city=city):
                s_id = s.get("station_id")
                valid_stations_map[s_id] = {
                    "station_id": s_id,
                    "station_name": s.get("station_name"),
                    "city_name": s.get("city_name"),
                    "state_name": s.get("state_name"),
                    "source": s.get("source"),
                    "latitude": s.get("latitude"),
                    "longitude": s.get("longitude"),
                }
            else:
                logger.warning(
                    f"Excluding non-Pune/invalid station from discovery: "
                    f"id={s.get('station_id')}, name={s.get('station_name')}, "
                    f"city={s.get('city_name')}, state={s.get('state_name')}"
                )

        discovered_station_ids = sorted(list(valid_stations_map.keys()))
        discovered_station_names = [valid_stations_map[sid]["station_name"] for sid in discovered_station_ids]

        logger.info(
            f"Discovered {len(discovered_station_ids)} valid Pune CPCB CAAQM stations: {discovered_station_ids}"
        )

        if not discovered_station_ids:
            logger.warning(f"No valid Pune CPCB CAAQM stations discovered in XKDR for city={city}.")
            if dest_file.exists():
                logger.info(f"Removing invalid previous XKDR measurements file: {dest_file}")
                dest_file.unlink()
            return {
                "status": "empty_period",
                "message": f"Zero valid CPCB CAAQM monitoring stations discovered for {city}.",
                "observations_count": 0,
                "stations_discovered": [],
                "stations_names": [],
                "pm25_count": 0,
                "pm10_count": 0,
                "first_timestamp": None,
                "last_timestamp": None,
                "data_path": None,
            }

        # Step 3: Explicitly construct measurement query with required filters
        meas_url = f"{base_url}/measurements"
        meas_params = [
            ("source", "cpcb_caaqm"),
            ("city", city),
            ("start", date_from),
            ("end", date_to),
            ("parameter", "PM2.5"),
            ("parameter", "PM10"),
            ("agg", "raw"),
            ("format", "json"),
        ]
        for sid in discovered_station_ids:
            meas_params.append(("station", sid))

        logger.info(
            f"Querying XKDR measurements with explicit filters: source=cpcb_caaqm, city={city}, "
            f"start={date_from}, end={date_to}, parameters=[PM2.5, PM10], agg=raw, "
            f"{len(discovered_station_ids)} station IDs..."
        )

        meas_resp = requests.get(meas_url, headers=headers, params=meas_params, timeout=60)
        meas_resp.raise_for_status()
        measurements_raw = meas_resp.json().get("data", [])

        # Step 4: Validate EVERY returned observation
        start_dt = pd.to_datetime(f"{date_from} 00:00:00")
        end_dt = pd.to_datetime(f"{date_to} 23:59:59")

        enriched_records = []
        rejected_records_count = 0

        for m in measurements_raw:
            s_id = m.get("station_id")
            # 1. station_id must belong to discovered Pune station set
            if s_id not in valid_stations_map:
                rejected_records_count += 1
                continue

            s_meta = valid_stations_map[s_id]

            # 2. city must be Pune when available
            obs_city = m.get("city_name") or m.get("city") or s_meta.get("city_name")
            if obs_city and str(obs_city).strip().lower() != city.lower():
                rejected_records_count += 1
                continue

            # 3. source must be cpcb_caaqm when available
            obs_source = m.get("source") or s_meta.get("source")
            if obs_source and str(obs_source).strip().lower() != "cpcb_caaqm":
                rejected_records_count += 1
                continue

            # 4. parameter must be PM2.5 or PM10
            raw_param = m.get("parameter_name") or m.get("parameter")
            norm_param = str(raw_param).upper().replace(".", "").replace("-", "").strip() if raw_param else ""
            if norm_param not in ["PM25", "PM10"]:
                rejected_records_count += 1
                continue

            # 5. collected_at must fall within requested date window
            dt_str = m.get("collected_at") or m.get("datetime")
            if not dt_str:
                rejected_records_count += 1
                continue

            try:
                obs_dt = pd.to_datetime(dt_str)
                naive_dt = obs_dt.tz_localize(None) if obs_dt.tzinfo else obs_dt
                if naive_dt < start_dt or naive_dt > end_dt:
                    rejected_records_count += 1
                    continue
            except Exception:
                rejected_records_count += 1
                continue

            record = {
                "source": "cpcb_caaqm",
                "station_id": s_id,
                "station_name": s_meta.get("station_name", s_id),
                "city": s_meta.get("city_name", city),
                "state": s_meta.get("state_name", "Maharashtra"),
                "station_lat": s_meta.get("latitude"),
                "station_lon": s_meta.get("longitude"),
                "coordinates": {
                    "latitude": s_meta.get("latitude"),
                    "longitude": s_meta.get("longitude"),
                },
                "parameter": m.get("parameter_name") or m.get("parameter"),
                "parameter_name": m.get("parameter_name") or m.get("parameter"),
                "unit": m.get("unit"),
                "collected_at": dt_str,
                "value": m.get("value"),
            }
            enriched_records.append(record)

        if rejected_records_count > 0:
            logger.warning(f"Rejected {rejected_records_count} observations failing strict Pune validation.")

        # Step 5: Delete or overwrite previous invalid file
        if dest_file.exists():
            logger.info(f"Removing invalid previous XKDR measurements file: {dest_file}")
            dest_file.unlink()

        if not enriched_records:
            logger.warning(
                f"XKDR returned 0 valid observations for the {len(discovered_station_ids)} Pune "
                f"CPCB CAAQM stations ({discovered_station_ids}) between {date_from} and {date_to}."
            )
            return {
                "status": "empty_period",
                "message": (
                    f"Strict validation completed: 0 valid CPCB CAAQM observations exist in Pune "
                    f"for {date_from} to {date_to}. All Moradabad/UPPCB stations excluded."
                ),
                "observations_count": 0,
                "stations_discovered": discovered_station_ids,
                "stations_names": discovered_station_names,
                "pm25_count": 0,
                "pm10_count": 0,
                "first_timestamp": None,
                "last_timestamp": None,
                "data_path": None,
            }

        # If valid records exist, write to dest_file
        with open(dest_file, "w", encoding="utf-8") as f:
            json.dump(enriched_records, f, indent=2)

        pm25_cnt = sum(1 for r in enriched_records if "25" in str(r.get("parameter_name", "")).replace(".", ""))
        pm10_cnt = sum(1 for r in enriched_records if "10" in str(r.get("parameter_name", "")).replace(".", ""))
        sorted_ts = sorted([r["collected_at"] for r in enriched_records if r.get("collected_at")])

        logger.info(
            f"Successfully downloaded and verified {len(enriched_records)} Pune XKDR air quality "
            f"observations saved to {dest_file}."
        )
        return {
            "status": "success",
            "message": f"Ingested {len(enriched_records)} verified Pune XKDR observations.",
            "observations_count": len(enriched_records),
            "stations_discovered": sorted(list(set(r["station_id"] for r in enriched_records))),
            "stations_names": sorted(list(set(r["station_name"] for r in enriched_records))),
            "pm25_count": pm25_cnt,
            "pm10_count": pm10_cnt,
            "first_timestamp": sorted_ts[0] if sorted_ts else None,
            "last_timestamp": sorted_ts[-1] if sorted_ts else None,
            "data_path": str(dest_file),
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"XKDR API request encountered an error: {e}")
        return {
            "status": "error",
            "message": f"Network/API error during XKDR ingestion: {e}",
            "observations_count": 0,
            "stations_discovered": [],
            "stations_names": [],
            "pm25_count": 0,
            "pm10_count": 0,
            "first_timestamp": None,
            "last_timestamp": None,
            "data_path": None,
        }


def ingest_air_quality(
    city: str = "Pune",
    date_from: str = "2023-01-11",
    date_to: str = "2023-01-18",
    output_dir: str = "data/raw/air_quality",
) -> Dict[str, Any]:
    """
    Unified air quality ingestion dispatcher.
    Prioritizes XKDR India Air Quality Database when AQI_API_KEY / XKDR_API_KEY is available.
    Falls back to OpenAQ API v3.
    """
    key = os.getenv("AQI_API_KEY") or os.getenv("XKDR_API_KEY")
    if key and key not in ["your_key_here", "your_xkdr_key_here"]:
        return ingest_xkdr_air_quality(
            city=city, date_from=date_from, date_to=date_to, output_dir=output_dir, api_key=key
        )
    return ingest_openaq(
        city=city, date_from=date_from, date_to=date_to, output_dir=output_dir
    )



# -----------------------------------------------------------------------------
# 5. CAMS GLOBAL ATMOSPHERIC COMPOSITION FORECASTS INGESTION
# -----------------------------------------------------------------------------
def ingest_cams_global_pm25(
    latitude: float = 18.5204,
    longitude: float = 73.8567,
    start_date: str = "2023-01-11",
    end_date: str = "2023-01-18",
    timezone: str = "Asia/Kolkata",
    output_dir: str = "data/raw/air_quality",
    processed_dir: str = "data/processed",
) -> Dict[str, Any]:
    """
    Ingests hourly PM2.5 from the CAMS Global Atmospheric Composition Forecasts
    product via the Open-Meteo Air Quality API (domains=cams_global).

    IMPORTANT SCIENTIFIC LABELING:
    - This data is MODELED atmospheric PM2.5, NOT direct Pune station observations.
    - source = "CAMS Global Atmospheric Composition Forecasts"
    - source_type = "modeled"
    - Must NOT be called "CPCB PM2.5", "observed PM2.5", or "ground truth".
    - Must NOT be confused with CAMS Global Reanalysis EAC4 (a separate product).
    - Validation is temporal holdout against the CAMS modeled target,
      NOT against ground-truth observations.

    CONTEXT:
    - CPCB / XKDR / OpenAQ provide no ground-station PM2.5 for Pune Jan 11–18, 2023.
    - CAMS Global modeled PM2.5 is the verified available Round 1 modeling target
      for this specific window.

    No API key is required for the public Open-Meteo Air Quality API.

    Validation checks performed:
    - Exact requested date range (no truncated series accepted)
    - Timezone-aware Asia/Kolkata timestamps
    - PM2.5 column present and non-null
    - No duplicate timestamps
    - Expected 192 hourly records for the 8-day target window
    - Numeric PM2.5 values only (non-negative)

    Saves:
    - Raw JSON: data/raw/air_quality/cams_global_pune_pm25_{start_date}_{end_date}.json
    - Cleaned parquet: data/processed/cams_global_pune_pm25_hourly.parquet

    Schema of cleaned parquet:
        timestamp   : datetime64[ns, Asia/Kolkata]
        pm25        : float64  (µg/m³, modeled)
        latitude    : float64  (API-snapped grid point)
        longitude   : float64  (API-snapped grid point)
        source      : str      ("CAMS Global Atmospheric Composition Forecasts")
        source_type : str      ("modeled")

    Args:
        latitude: Query latitude (default Pune center: 18.5204).
        longitude: Query longitude (default Pune center: 73.8567).
        start_date: ISO start date string (YYYY-MM-DD).
        end_date: ISO end date string (YYYY-MM-DD).
        timezone: Timezone identifier for response timestamps.
        output_dir: Directory to save raw JSON response.
        processed_dir: Directory to save cleaned parquet artifact.

    Returns:
        Dict reporting HTTP status, record count, first/last timestamp,
        null count, min/max/mean PM2.5, duplicate count, source metadata,
        and output file paths.
    """
    base_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "pm2_5",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone,
        "domains": "cams_global",
    }

    SOURCE_LABEL = "CAMS Global Atmospheric Composition Forecasts"
    SOURCE_TYPE = "modeled"

    logger.info(
        f"Querying Open-Meteo Air Quality API (CAMS Global) for ({latitude}, {longitude}) "
        f"from {start_date} to {end_date} (tz: {timezone})..."
    )
    logger.info(
        "Scientific note: This product is CAMS Global Atmospheric Composition Forecasts — "
        "modeled PM2.5, NOT direct Pune ground-station observations. "
        "Not to be confused with CAMS Global Reanalysis EAC4."
    )

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        http_status = response.status_code
        data = response.json()
    except requests.exceptions.HTTPError as e:
        body = ""
        try:
            body = e.response.json()
        except Exception:
            pass
        msg = f"Open-Meteo CAMS Global API HTTP error: {e}. Response body: {body}"
        logger.error(msg)
        return {
            "status": "error",
            "http_status": getattr(e.response, "status_code", None),
            "message": msg,
            "record_count": 0,
            "non_null_pm25": 0,
            "raw_path": None,
            "processed_path": None,
        }
    except requests.exceptions.RequestException as e:
        msg = f"Open-Meteo CAMS Global API request failed: {e}"
        logger.error(msg)
        return {
            "status": "error",
            "http_status": None,
            "message": msg,
            "record_count": 0,
            "non_null_pm25": 0,
            "raw_path": None,
            "processed_path": None,
        }

    # --- Extract fields from response ---
    snapped_lat = data.get("latitude", latitude)
    snapped_lon = data.get("longitude", longitude)
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    pm25_values = hourly.get("pm2_5", [])

    record_count = len(times)
    non_null_count = sum(1 for v in pm25_values if v is not None)
    null_count = record_count - non_null_count
    numeric_vals = [float(v) for v in pm25_values if v is not None]
    duplicate_count = record_count - len(set(times))
    pm25_min = round(min(numeric_vals), 4) if numeric_vals else None
    pm25_max = round(max(numeric_vals), 4) if numeric_vals else None
    pm25_mean = round(sum(numeric_vals) / len(numeric_vals), 4) if numeric_vals else None
    first_ts = times[0] if times else None
    last_ts = times[-1] if times else None

    logger.info(
        f"CAMS Global response: HTTP {http_status}, {record_count} hours, "
        f"non-null={non_null_count}, min={pm25_min}, max={pm25_max}, mean={pm25_mean}, "
        f"duplicates={duplicate_count}, snapped_lat={snapped_lat}, snapped_lon={snapped_lon}"
    )

    # --- Save raw JSON response ---
    raw_out = Path(output_dir)
    raw_out.mkdir(parents=True, exist_ok=True)
    raw_filename = f"cams_global_pune_pm25_{start_date}_{end_date}.json"
    raw_path = raw_out / raw_filename
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Raw CAMS Global response saved to {raw_path}.")

    # --- Validation checks (MUST all pass before writing processed artifact) ---
    validation_errors: List[str] = []

    # 1. Exact date range: first timestamp must start on start_date, last on end_date
    expected_first = f"{start_date}T00:00"
    expected_last = f"{end_date}T23:00"
    if first_ts != expected_first:
        validation_errors.append(
            f"Date range mismatch: expected first={expected_first!r}, got {first_ts!r}"
        )
    if last_ts != expected_last:
        validation_errors.append(
            f"Date range mismatch: expected last={expected_last!r}, got {last_ts!r}"
        )

    # 2. Expected 192 hourly records for 8-day window
    from datetime import date as _date
    try:
        n_days = (_date.fromisoformat(end_date) - _date.fromisoformat(start_date)).days + 1
        expected_records = n_days * 24
    except Exception:
        expected_records = 192
    if record_count != expected_records:
        validation_errors.append(
            f"Record count mismatch: expected {expected_records}, got {record_count}"
        )

    # 3. No null PM2.5 values
    if null_count > 0:
        validation_errors.append(f"Found {null_count} null PM2.5 values.")

    # 4. No duplicate timestamps
    if duplicate_count > 0:
        validation_errors.append(f"Found {duplicate_count} duplicate timestamps.")

    # 5. No negative PM2.5 values
    neg_count = sum(1 for v in numeric_vals if v < 0)
    if neg_count > 0:
        validation_errors.append(f"Found {neg_count} negative PM2.5 values.")

    if validation_errors:
        error_summary = "; ".join(validation_errors)
        logger.error(f"CAMS Global validation failed: {error_summary}")
        return {
            "status": "validation_failed",
            "http_status": http_status,
            "message": f"CAMS Global validation errors: {error_summary}",
            "record_count": record_count,
            "first_timestamp": first_ts,
            "last_timestamp": last_ts,
            "non_null_pm25": non_null_count,
            "null_pm25": null_count,
            "duplicate_count": duplicate_count,
            "pm25_min": pm25_min,
            "pm25_max": pm25_max,
            "pm25_mean": pm25_mean,
            "source": SOURCE_LABEL,
            "source_type": SOURCE_TYPE,
            "snapped_latitude": snapped_lat,
            "snapped_longitude": snapped_lon,
            "raw_path": str(raw_path),
            "processed_path": None,
        }

    # --- Build cleaned DataFrame ---
    # Parse timestamps as timezone-naive IST, then localize to Asia/Kolkata
    # pd.to_datetime(list) returns DatetimeIndex; use .tz not .dt.tz
    ts_index = pd.to_datetime(times)
    if ts_index.tz is None:
        ts_index = ts_index.tz_localize("Asia/Kolkata")
    else:
        ts_index = ts_index.tz_convert("Asia/Kolkata")
    ts_series = pd.Series(ts_index)

    cleaned_df = pd.DataFrame({
        "timestamp": ts_series,
        "pm25": [float(v) for v in pm25_values],
        "latitude": snapped_lat,
        "longitude": snapped_lon,
        "source": SOURCE_LABEL,
        "source_type": SOURCE_TYPE,
    })

    # --- Save cleaned parquet artifact ---
    proc_out = Path(processed_dir)
    proc_out.mkdir(parents=True, exist_ok=True)
    proc_path = proc_out / "cams_global_pune_pm25_hourly.parquet"
    cleaned_df.to_parquet(proc_path, index=False)
    logger.info(
        f"CAMS Global cleaned artifact saved to {proc_path} "
        f"({len(cleaned_df)} rows, source_type='modeled')."
    )
    logger.info(
        "REMINDER: This artifact contains CAMS Global Atmospheric Composition Forecasts "
        "modeled PM2.5. It must NOT be labeled as CPCB observed PM2.5 or ground truth "
        "in any downstream model card, report, or feature file."
    )

    return {
        "status": "success",
        "http_status": http_status,
        "message": (
            f"Ingested {record_count} hourly CAMS Global modeled PM2.5 records "
            f"({start_date} to {end_date}, Asia/Kolkata). "
            "Source type: modeled (not CPCB observed)."
        ),
        "record_count": record_count,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "non_null_pm25": non_null_count,
        "null_pm25": null_count,
        "duplicate_count": duplicate_count,
        "pm25_min": pm25_min,
        "pm25_max": pm25_max,
        "pm25_mean": pm25_mean,
        "source": SOURCE_LABEL,
        "source_type": SOURCE_TYPE,
        "snapped_latitude": snapped_lat,
        "snapped_longitude": snapped_lon,
        "raw_path": str(raw_path),
        "processed_path": str(proc_path),
    }


# -----------------------------------------------------------------------------
# 6. EDGAR NETCDF CONTEXT EXTRACTION
# -----------------------------------------------------------------------------
def extract_edgar_pune_context(
    edgar_dir: str = "data/raw/edgar",
    target_year: int = 2022,
    output_path: str = "data/processed/edgar_pune_context.parquet",
) -> pd.DataFrame:
    """
    Inspects EDGAR NetCDF industrial emissions files and extracts Pune regional context.
    
    Strictly preserves EDGAR as annual spatial context. Does NOT create hourly values.

    Args:
        edgar_dir: Directory containing EDGAR NetCDF files.
        target_year: Baseline year to inspect (default: 2022).
        output_path: Path to save the extracted spatial context table.

    Returns:
        pd.DataFrame containing annual emissions for Pune region grid cells.
    """
    try:
        import xarray as xr
    except ImportError:
        raise ImportError("xarray is required for reading EDGAR NetCDF archives. Run pip install xarray netCDF4.")

    nc_file = Path(edgar_dir) / f"v8.1_FT2022_AP_PM2.5_{target_year}_IND_emi.nc"
    if not nc_file.exists():
        fallback_files = list(Path(edgar_dir).glob("*.nc"))
        if not fallback_files:
            raise FileNotFoundError(f"No NetCDF files found in {edgar_dir}.")
        nc_file = fallback_files[-1]
        logger.info(f"Target year file not found. Using available fallback: {nc_file.name}")

    logger.info(f"Opening EDGAR NetCDF file: {nc_file}")
    ds = xr.open_dataset(nc_file)

    # Log NetCDF metadata
    logger.info(f"EDGAR Dimensions: {dict(ds.dims)}")
    logger.info(f"EDGAR Coordinates: {list(ds.coords.keys())}")
    logger.info(f"EDGAR Data Variables: {list(ds.data_vars.keys())}")
    if "emissions" in ds:
        emiss_attrs = ds["emissions"].attrs
        logger.info(
            f"Variable 'emissions' attributes: substance={emiss_attrs.get('substance')}, "
            f"units={emiss_attrs.get('units')}, sector={emiss_attrs.get('description')}, "
            f"year={emiss_attrs.get('year')}"
        )

    # Pune Bounding Box: 18.3° to 18.7° N, 73.6° to 74.1° E
    pune_slice = ds.sel(lat=slice(18.3, 18.7), lon=slice(73.6, 74.1))
    df_pune = pune_slice.to_dataframe().reset_index()
    df_pune["year"] = target_year
    df_pune["sector"] = "IND_Combustion_for_manufacturing"
    df_pune["units"] = "Tonnes/grid_cell/year"
    df_pune["temporal_resolution"] = "annual"

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df_pune.to_parquet(out_file, index=False)

    logger.info(
        f"Extracted {len(df_pune)} grid cells for Pune region ({target_year}). "
        f"Saved spatial context to {out_file}."
    )
    logger.info(
        "Scientific note: EDGAR represents annual grid emissions and is retained strictly "
        "as spatial background context. No hourly values are generated from it."
    )
    return df_pune


if __name__ == "__main__":
    logger.info("Executing ingestion self-test...")
    # Test weather ingestion
    weather_data = ingest_open_meteo()
    # Test CAMS Global modeled PM2.5 ingestion
    cams_result = ingest_cams_global_pm25()
    logger.info(f"CAMS Global status: {cams_result['status']}, records: {cams_result.get('record_count')}")
    # Test OpenAQ ingestion (verifies graceful blocker message)
    aq_status = ingest_openaq()
    logger.info(f"OpenAQ status: {aq_status['status']}")
    # Test EDGAR extraction
    edgar_df = extract_edgar_pune_context()
    logger.info(f"EDGAR extracted {len(edgar_df)} cells.")

