"""
Unit and Integration Tests for AERIS Data/ML Pipeline (tests/test_data_pipeline.py)
===================================================================================
Tests core pipeline invariants:
1. Missing traffic measurements are excluded and NEVER become zero to cause false deltas
2. First-row baseline behavior: starting counter values establish baseline (delta = 0)
3. Session reset handling: continuation files establish independent session boundaries
4. Invalid weather values are excluded/flagged rather than silently clipped
5. Timezone consistency across traffic, weather, and OpenAQ (Asia/Kolkata)
6. Equivalence between streaming and non-streaming traffic cleaning on a small fixture
7. Haversine distance spatial mapping threshold
8. Strict gating of aeris_features.parquet when real AQ data is absent
9. Schema validation and duplicate key detection
10. Graceful OpenAQ missing key handling
11. CAMS Global modeled PM2.5 ingestion (192-hour series, validation, source labeling)
12. No future-target leakage in ML feature construction
"""

import io
import math
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.src.clean import (
    clean_air_quality_data,
    clean_traffic_data,
    clean_traffic_session,
    clean_traffic_stream,
    clean_weather_data,
)
from ml.src.features import (
    AIR_QUALITY_DISTANCE_THRESHOLD_KM,
    CITY_FEATURE_COLUMNS,
    CITY_TARGET_COLUMN,
    ZONE_COORDINATES,
    build_city_level_ml_dataset,
    build_hourly_traffic_features,
    build_ml_features,
    build_unified_features,
    build_zone_traffic_summary,
    calculate_persistence_baseline,
    haversine_distance_km,
    map_air_quality_to_zones,
)
from ml.src.ingest import (
    ingest_cams_global_pm25,
    ingest_openaq,
    ingest_xkdr_air_quality,
    is_valid_pune_cpcb_station,
)



class TestTrafficCleaningPolicies:
    def test_missing_traffic_count_does_not_become_zero_and_produce_false_delta(self):
        """
        Critical Policy Test:
        Missing vehicle count values must NOT be imputed as zero.
        Imputing zero into a cumulative counter stream would cause an artificial positive delta spike.
        Instead, rows with missing counts are excluded, preventing false delta creation.
        """
        mock_raw = pd.DataFrame([
            {"date": "2023-01-11", "Time": "09:00:00", "Direction": "UP",
             "car": 100, "motorbike": 10, "bus": 2, "truck": 1,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
            # Corrupted / missing observation: car is NaN
            {"date": "2023-01-11", "Time": "09:00:01", "Direction": "UP",
             "car": np.nan, "motorbike": 10, "bus": 2, "truck": 1,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
            # Normal next observation: car increments to 101
            {"date": "2023-01-11", "Time": "09:00:02", "Direction": "UP",
             "car": 101, "motorbike": 10, "bus": 2, "truck": 1,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
        ])

        clean_df, audit = clean_traffic_data(mock_raw)

        # Audit must explicitly record the excluded missing measurement
        assert audit["missing_measurement_rows"] == 1
        assert len(clean_df) == 2

        # Delta must be 101 - 100 = 1, NOT 101 - 0 = 101!
        assert clean_df["delta_car"].max() == 1.0
        assert clean_df["traffic_count"].sum() == 1.0

    def test_first_row_baseline_behavior(self):
        """
        Tests that the first observation in a session establishes the initial counter baseline.
        The delta for the first observation must be 0.0, not the full starting count value.
        """
        mock_raw = pd.DataFrame([
            # Session starts with non-zero counter values
            {"date": "2023-01-11", "Time": "09:00:00", "Direction": "UP",
             "car": 50, "motorbike": 20, "bus": 5, "truck": 2,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
            # Next observation: 2 new cars detected
            {"date": "2023-01-11", "Time": "09:00:01", "Direction": "UP",
             "car": 52, "motorbike": 20, "bus": 5, "truck": 2,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
        ])

        clean_df, audit = clean_traffic_data(mock_raw)
        assert len(clean_df) == 2

        # First row delta must be 0.0 (baseline established)
        assert clean_df["delta_car"].iloc[0] == 0.0
        assert clean_df["traffic_count"].iloc[0] == 0.0

        # Second row delta must be 2.0
        assert clean_df["delta_car"].iloc[1] == 2.0
        assert clean_df["traffic_count"].iloc[1] == 2.0

        # Total vehicles counted across the session must be 2.0, NOT 79.0 (50+20+5+2+2)
        assert clean_df["traffic_count"].sum() == 2.0
        assert audit["total_vehicles_counted"] == 2.0

    def test_session_reset_handling(self):
        """
        Tests that continuation files (_one.csv) reset their baseline cleanly.
        session_file acts as an explicit session boundary preventing false jumps.
        """
        mock_raw = pd.DataFrame([
            # Primary file ending at count 300
            {"date": "2023-01-11", "Time": "11:24:00", "Direction": "UP",
             "car": 295, "motorbike": 50, "bus": 10, "truck": 5,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
            {"date": "2023-01-11", "Time": "11:24:01", "Direction": "UP",
             "car": 300, "motorbike": 50, "bus": 10, "truck": 5,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
            # Continuation file starts at 0
            {"date": "2023-01-11", "Time": "11:26:00", "Direction": "UP",
             "car": 0, "motorbike": 0, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11_one.csv"},
            {"date": "2023-01-11", "Time": "11:26:01", "Direction": "UP",
             "car": 3, "motorbike": 1, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11_one.csv"},
        ])

        clean_df, audit = clean_traffic_data(mock_raw)
        assert len(clean_df) == 4

        # Verify no negative deltas and no spike from 300 -> 0
        assert (clean_df["traffic_count"] >= 0).all()
        # Session 1 delta: (300-295) = 5
        # Session 2 delta: (3-0) + (1-0) = 4
        # Total vehicles across both sessions: 5 + 4 = 9.0
        assert clean_df["traffic_count"].sum() == 9.0

    def test_same_timestamp_source_order_preserved(self):
        """
        Regression Test:
        Validates that when multiple observations share the exact same timestamp
        within a session and direction, they are sorted by _source_row to preserve
        the original CSV source row order and produce expected deltas.
        """
        # Case 1: Pass intentionally out-of-order in the DataFrame to verify
        # that clean_traffic_session sorts by ["Direction", "timestamp", "_source_row"]
        mock_shuffled = pd.DataFrame([
            # Shuffled: source row 1 appears first in input list
            {"date": "2023-01-11", "Time": "09:00:00", "Direction": "UP",
             "car": 14, "motorbike": 8, "bus": 1, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv",
             "_source_row": 1},
            # Shuffled: source row 0 appears second in input list
            {"date": "2023-01-11", "Time": "09:00:00", "Direction": "UP",
             "car": 10, "motorbike": 5, "bus": 1, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv",
             "_source_row": 0},
        ])

        clean_df, audit = clean_traffic_session(mock_shuffled, session_file="a2_11.csv")

        assert len(clean_df) == 2
        # Source row 0 must be ordered first, establishing the baseline
        assert clean_df.iloc[0]["_source_row"] == 0
        assert clean_df.iloc[0]["car_raw"] == 10
        assert clean_df.iloc[0]["delta_car"] == 0.0
        assert clean_df.iloc[0]["traffic_count"] == 0.0

        # Source row 1 must be ordered second, producing expected positive deltas:
        # delta_car = 14 - 10 = 4.0
        # delta_motorbike = 8 - 5 = 3.0
        # traffic_count = 4.0 + 3.0 = 7.0
        assert clean_df.iloc[1]["_source_row"] == 1
        assert clean_df.iloc[1]["car_raw"] == 14
        assert clean_df.iloc[1]["delta_car"] == 4.0
        assert clean_df.iloc[1]["delta_motorbike"] == 3.0
        assert clean_df.iloc[1]["traffic_count"] == 7.0
        assert audit["total_vehicles_counted"] == 7.0

        # Case 2: Full session through clean_traffic_data without manual _source_row
        # Automatic source-order preservation for same-timestamp rows in CSV order
        mock_raw = pd.DataFrame([
            {"date": "2023-01-11", "Time": "09:00:00", "Direction": "UP",
             "car": 10, "motorbike": 5, "bus": 1, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
            {"date": "2023-01-11", "Time": "09:00:00", "Direction": "UP",
             "car": 15, "motorbike": 7, "bus": 1, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"},
        ])
        clean_df2, audit2 = clean_traffic_data(mock_raw)
        assert len(clean_df2) == 2
        assert clean_df2.iloc[0]["delta_car"] == 0.0
        assert clean_df2.iloc[1]["delta_car"] == 5.0
        assert clean_df2.iloc[1]["traffic_count"] == 7.0  # (15-10) + (7-5)
        assert audit2["total_vehicles_counted"] == 7.0

    def test_equivalence_streaming_and_non_streaming_traffic_cleaning(self, tmp_path):
        """
        Tests that clean_traffic_stream and clean_traffic_data produce equivalent
        cleaned rows and deltas when given the same input data.
        """
        # Create a mock zip archive containing two session CSVs
        zip_path = tmp_path / "mock_traffic.zip"
        csv1_content = (
            "Time,Direction,car,motorbike,bus,truck\n"
            "09:00:00,UP,0,0,0,0\n"
            "09:00:01,UP,2,1,0,0\n"
            "09:00:02,UP,5,3,1,0\n"
        )
        csv2_content = (
            "Time,Direction,car,motorbike,bus,truck\n"
            "09:00:00,DOWN,0,0,0,0\n"
            "09:00:01,DOWN,1,0,0,0\n"
            "09:00:02,DOWN,4,2,0,1\n"
        )

        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("traffic/AlankarChowk/a2/a2_11.csv", csv1_content)
            z.writestr("traffic/AlankarChowk/a2/a2_12.csv", csv2_content)

        # 1. Clean via streaming (aggregate_hourly=False to inspect row-level equivalence)
        stream_df, stream_audit = clean_traffic_stream(
            traffic_zip_path=str(zip_path), aggregate_hourly=False
        )

        # 2. Clean via non-streaming DataFrame
        df1 = pd.read_csv(io.StringIO(csv1_content))
        df1["junction"] = "AlankarChowk"
        df1["camera_id"] = "a2"
        df1["session_file"] = "a2_11.csv"
        df1["date"] = "2023-01-11"

        df2 = pd.read_csv(io.StringIO(csv2_content))
        df2["junction"] = "AlankarChowk"
        df2["camera_id"] = "a2"
        df2["session_file"] = "a2_12.csv"
        df2["date"] = "2023-01-12"

        raw_df = pd.concat([df1, df2], ignore_index=True)
        non_stream_df, non_stream_audit = clean_traffic_data(raw_df)

        # Sort both for deterministic comparison
        cols_to_compare = [
            "timestamp", "junction", "camera_id", "direction",
            "delta_car", "delta_motorbike", "delta_bus", "delta_truck", "traffic_count"
        ]
        s_sorted = stream_df.sort_values(["timestamp", "direction"]).reset_index(drop=True)[cols_to_compare]
        ns_sorted = non_stream_df.sort_values(["timestamp", "direction"]).reset_index(drop=True)[cols_to_compare]

        pd.testing.assert_frame_equal(s_sorted, ns_sorted)
        assert stream_audit["total_vehicles_counted"] == non_stream_audit["total_vehicles_counted"]


class TestWeatherCleaningPolicies:
    def test_invalid_weather_observations_excluded_not_clipped(self):
        """
        Critical Policy Test:
        Do not silently clip impossible observations into valid values.
        Out-of-range records must be flagged and excluded, and audited.
        """
        mock_raw = {
            "hourly": {
                "time": [
                    "2023-01-11T09:00",  # Valid
                    "2023-01-11T10:00",  # Invalid temp: 85°C (> 60°C)
                    "2023-01-11T11:00",  # Invalid humidity: -15% (< 0%)
                    "2023-01-11T12:00",  # Invalid wind: 350 km/h (> 200 km/h)
                    "2023-01-11T13:00",  # Invalid rainfall: -5 mm (< 0 mm)
                    "2023-01-11T14:00",  # Valid
                ],
                "temperature_2m": [25.0, 85.0, 26.0, 24.0, 23.0, 22.0],
                "relative_humidity_2m": [50.0, 45.0, -15.0, 40.0, 55.0, 60.0],
                "wind_speed_10m": [12.0, 15.0, 10.0, 350.0, 8.0, 9.0],
                "precipitation": [0.0, 0.0, 0.0, 0.0, -5.0, 0.5],
            }
        }

        clean_df, audit = clean_weather_data(mock_raw)

        # 4 out of 6 records were invalid and must be excluded, NOT clipped!
        assert audit["raw_hours_received"] == 6
        assert audit["total_invalid_hours_excluded"] == 4
        assert audit["invalid_temperature_count"] == 1
        assert audit["invalid_humidity_count"] == 1
        assert audit["invalid_wind_speed_count"] == 1
        assert audit["invalid_rainfall_count"] == 1
        assert audit["final_valid_hours"] == 2

        # Only the 2 completely valid hours (09:00 and 14:00) should remain
        assert len(clean_df) == 2
        # Verify 85.0 was NOT clipped to 60.0
        assert 60.0 not in clean_df["temperature"].values


class TestTimezoneConsistency:
    def test_timezone_consistency_across_sources(self):
        """Verifies that traffic, weather, and OpenAQ data all align to timezone Asia/Kolkata (+05:30)."""
        # 1. Traffic timezone
        mock_traffic = pd.DataFrame([{
            "date": "2023-01-11", "Time": "09:00:00", "Direction": "UP",
            "car": 10, "motorbike": 5, "bus": 1, "truck": 0,
            "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv"
        }])
        clean_t, _ = clean_traffic_data(mock_traffic)
        assert str(clean_t["timestamp"].dt.tz) == "Asia/Kolkata" or "+05:30" in str(clean_t["timestamp"].dt.tz)

        # 2. Weather timezone
        mock_weather = {
            "hourly": {
                "time": ["2023-01-11T09:00"],
                "temperature_2m": [22.0],
                "relative_humidity_2m": [50.0],
                "wind_speed_10m": [10.0],
                "precipitation": [0.0],
            }
        }
        clean_w, _ = clean_weather_data(mock_weather)
        assert str(clean_w["timestamp"].dt.tz) == "Asia/Kolkata" or "+05:30" in str(clean_w["timestamp"].dt.tz)

        # 3. OpenAQ UTC to Asia/Kolkata conversion
        mock_aq_raw = [{
            "value": 75.0,
            "parameter": {"name": "pm25"},
            "period": {"datetimeFrom": {"utc": "2023-01-11T03:30:00Z"}},
            "coordinates": {"latitude": 18.531, "longitude": 73.845},
            "location_id": 11613,
            "location_name": "Shivajinagar",
        }]
        clean_aq, _ = clean_air_quality_data(mock_aq_raw)
        assert not clean_aq.empty
        # 03:30:00 UTC == 09:00:00 Asia/Kolkata
        assert clean_aq["timestamp"].iloc[0].hour == 9
        assert clean_aq["timestamp"].iloc[0].minute == 0
        assert str(clean_aq["timestamp"].dt.tz) == "Asia/Kolkata" or "+05:30" in str(clean_aq["timestamp"].dt.tz)


class TestSpatialAndGating:
    def test_haversine_distance(self):
        """Verifies Haversine formula against known Pune coordinates."""
        d = haversine_distance_km(18.5310, 73.8450, 18.5314, 73.8648)
        assert 1.9 < d < 2.3

    def test_air_quality_distance_threshold_mapping(self):
        """Tests that stations within threshold map to zones, while distant stations are excluded."""
        mock_aq = pd.DataFrame([
            # Close station: Shivajinagar (~2.1 km to RTO Chowk)
            {"timestamp": pd.to_datetime("2023-01-11 09:00:00+05:30"), "station_id": 1,
             "station_name": "Shivajinagar", "station_lat": 18.5310, "station_lon": 73.8450,
             "pm25": 85.0, "pm10": 140.0},
            # Distant station: Bhosari (~10.8 km, exceeds 5.0 km threshold)
            {"timestamp": pd.to_datetime("2023-01-11 09:00:00+05:30"), "station_id": 2,
             "station_name": "Bhosari", "station_lat": 18.6270, "station_lon": 73.8470,
             "pm25": 110.0, "pm10": 190.0},
        ])

        mapped = map_air_quality_to_zones(mock_aq, threshold_km=5.0)
        assert not mapped.empty
        # Only Shivajinagar should be mapped
        assert (mapped["station_name"] == "Shivajinagar").all()
        assert "Bhosari" not in mapped["station_name"].values
        assert (mapped["distance_to_zone_km"] <= 5.0).all()

    def test_strict_gating_without_real_pm25(self, tmp_path):
        """Verifies that aeris_features.parquet is NOT created when real PM2.5 data is absent."""
        mock_weather = pd.DataFrame([{
            "timestamp": pd.to_datetime("2023-01-11 09:00:00+05:30"),
            "temperature": 22.0, "humidity": 50.0, "wind_speed": 10.0, "rainfall": 0.0
        }])
        mock_traffic = pd.DataFrame([{
            "timestamp": pd.to_datetime("2023-01-11 09:00:00+05:30"),
            "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv",
            "direction": "UP", "car_raw": 10, "motorbike_raw": 5, "bus_raw": 1, "truck_raw": 0,
            "delta_car": 2, "delta_motorbike": 1, "delta_bus": 0, "delta_truck": 0, "traffic_count": 3
        }])

        empty_aq = pd.DataFrame(columns=["timestamp", "pm25", "pm10"])
        report = build_unified_features(
            traffic_df=mock_traffic,
            weather_df=mock_weather,
            aq_df=empty_aq,
            output_dir=str(tmp_path),
        )

        assert report["status"] == "gated_missing_air_quality"
        assert report["aeris_features_path"] is None
        assert not (tmp_path / "aeris_features.parquet").exists()
        # Intermediate tables must still be saved
        assert (tmp_path / "traffic_clean.parquet").exists()
        assert (tmp_path / "traffic_hourly.parquet").exists()
        assert (tmp_path / "weather_hourly.parquet").exists()

    def test_openaq_missing_key_graceful_block(self, monkeypatch):
        """Verifies that ingest_openaq safely detects missing key and blocks execution without raising unhandled errors."""
        monkeypatch.setenv("OPENAQ_API_KEY", "")
        res = ingest_openaq(api_key="")
        assert res["status"] == "blocked"
        assert res["observations_count"] == 0
        assert "OPENAQ_API_KEY" in res["message"]

    def test_schema_and_duplicate_keys_when_real_aq_provided(self, tmp_path):
        """Verifies target schema order and lack of duplicate keys when real AQ is merged."""
        mock_weather = pd.DataFrame([
            {"timestamp": pd.to_datetime("2023-01-11 09:00:00+05:30"),
             "temperature": 22.0, "humidity": 50.0, "wind_speed": 10.0, "rainfall": 0.0},
            {"timestamp": pd.to_datetime("2023-01-11 10:00:00+05:30"),
             "temperature": 24.0, "humidity": 45.0, "wind_speed": 11.0, "rainfall": 0.0},
        ])
        mock_traffic = pd.DataFrame([
            {"timestamp": pd.to_datetime("2023-01-11 09:15:00+05:30"),
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv",
             "direction": "UP", "car_raw": 10, "motorbike_raw": 5, "bus_raw": 1, "truck_raw": 0,
             "delta_car": 2, "delta_motorbike": 1, "delta_bus": 0, "delta_truck": 0, "traffic_count": 3},
            {"timestamp": pd.to_datetime("2023-01-11 10:15:00+05:30"),
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv",
             "direction": "UP", "car_raw": 15, "motorbike_raw": 8, "bus_raw": 1, "truck_raw": 0,
             "delta_car": 5, "delta_motorbike": 3, "delta_bus": 0, "delta_truck": 0, "traffic_count": 8},
        ])
        mock_aq = pd.DataFrame([
            {"timestamp": pd.to_datetime("2023-01-11 09:00:00+05:30"), "station_id": 1,
             "station_name": "Shivajinagar", "station_lat": 18.5310, "station_lon": 73.8450,
             "pm25": 82.5, "pm10": 135.0},
            {"timestamp": pd.to_datetime("2023-01-11 10:00:00+05:30"), "station_id": 1,
             "station_name": "Shivajinagar", "station_lat": 18.5310, "station_lon": 73.8450,
             "pm25": 90.0, "pm10": 150.0},
        ])

        report = build_unified_features(
            traffic_df=mock_traffic,
            weather_df=mock_weather,
            aq_df=mock_aq,
            output_dir=str(tmp_path),
        )

        assert report["status"] == "success"
        out_file = tmp_path / "aeris_features.parquet"
        assert out_file.exists()
        res_df = pd.read_parquet(out_file)

        expected_schema = [
            "timestamp", "zone_id", "latitude", "longitude",
            "pm25", "pm10", "temperature", "humidity",
            "wind_speed", "rainfall", "traffic_count",
            "pm25_source", "pm25_source_type",
        ]
        assert list(res_df.columns) == expected_schema
        assert not res_df.duplicated(subset=["timestamp", "zone_id"]).any()

    def test_xkdr_missing_key_graceful_block(self, monkeypatch):
        """Verifies that ingest_xkdr_air_quality safely detects missing key and blocks execution gracefully."""
        monkeypatch.setenv("AQI_API_KEY", "")
        monkeypatch.setenv("XKDR_API_KEY", "")
        res = ingest_xkdr_air_quality(api_key="")
        assert res["status"] == "blocked"
        assert res["observations_count"] == 0
        assert "AQI_API_KEY" in res["message"]

    def test_xkdr_air_quality_cleaning_pipeline(self):
        """Verifies that XKDR CPCB observation format is cleaned, normalized, and localized to Asia/Kolkata."""
        mock_xkdr_records = [
            {
                "source": "cpcb_caaqm",
                "station_id": "site_5409",
                "station_name": "Revenue Colony-Shivajinagar, Pune - IITM",
                "city": "Pune",
                "station_lat": 18.530085,
                "station_lon": 73.849598,
                "parameter_name": "PM2.5",
                "unit": "ug/m3",
                "collected_at": "2023-01-11T09:00:00",
                "value": 75.5,
            },
            {
                "source": "cpcb_caaqm",
                "station_id": "site_5409",
                "station_name": "Revenue Colony-Shivajinagar, Pune - IITM",
                "city": "Pune",
                "station_lat": 18.530085,
                "station_lon": 73.849598,
                "parameter_name": "PM10",
                "unit": "ug/m3",
                "collected_at": "2023-01-11T09:00:00",
                "value": 120.0,
            },
        ]
        clean_df, audit = clean_air_quality_data(mock_xkdr_records)

        assert audit["data_status"] == "present"
        assert audit["valid_pm25_records"] == 1
        assert audit["valid_pm10_records"] == 1
        assert len(clean_df) == 1

        row = clean_df.iloc[0]
        assert str(row["timestamp"].tz) == "Asia/Kolkata"
        assert row["pm25"] == 75.5
        assert row["pm10"] == 120.0
        assert row["station_id"] == "site_5409"
        assert row["station_lat"] == 18.530085

    def test_regression_moradabad_station_excluded_from_pune_discovery(self):
        """
        Regression Test 1:
        Verifies that Moradabad / UPPCB stations (including site_5613) are strictly
        rejected and NEVER included in Pune discovered station set or clean data.
        """
        moradabad_station = {
            "station_id": "site_5613",
            "station_name": "Transport Nagar, Moradabad - UPPCB",
            "city_name": "Pune",
            "state_name": "Maharashtra",
            "source": "cpcb_caaqm",
        }
        genuine_pune_station = {
            "station_id": "site_5409",
            "station_name": "Revenue Colony-Shivajinagar, Pune - IITM",
            "city_name": "Pune",
            "state_name": "Maharashtra",
            "source": "cpcb_caaqm",
        }
        assert not is_valid_pune_cpcb_station(moradabad_station)
        assert is_valid_pune_cpcb_station(genuine_pune_station)

        # In clean_air_quality_data, records with Moradabad must be rejected
        mock_records = [{
            "station_id": "site_5613",
            "station_name": "Transport Nagar, Moradabad - UPPCB",
            "parameter_name": "PM2.5",
            "collected_at": "2023-01-11T09:00:00",
            "value": 85.0,
        }]
        clean_df, audit = clean_air_quality_data(mock_records)
        assert clean_df.empty
        assert audit["valid_pm25_records"] == 0

    def test_regression_station_outside_discovered_pune_set_rejected(self, monkeypatch):
        """
        Regression Test 2:
        Verifies that observations from stations outside the discovered Pune station set
        are rejected.
        """
        class MockResponse:
            def __init__(self, data):
                self._data = data
                self.status_code = 200
            def json(self):
                return {"data": self._data}
            def raise_for_status(self):
                pass

        def mock_get(url, *args, **kwargs):
            if "stations" in url:
                return MockResponse([{
                    "station_id": "site_5409",
                    "station_name": "Revenue Colony-Shivajinagar, Pune - IITM",
                    "city_name": "Pune",
                    "state_name": "Maharashtra",
                    "source": "cpcb_caaqm",
                    "latitude": 18.53,
                    "longitude": 73.85,
                }])
            elif "measurements" in url:
                # Return observation from an undiscovered / foreign station (e.g. site_9999)
                return MockResponse([{
                    "station_id": "site_9999",
                    "parameter_name": "PM2.5",
                    "collected_at": "2023-01-11T09:00:00",
                    "value": 100.0,
                }])
            raise ValueError(f"Unexpected url: {url}")

        import requests
        monkeypatch.setattr(requests, "get", mock_get)

        res = ingest_xkdr_air_quality(api_key="mock_key")
        assert res["status"] == "empty_period"
        assert res["observations_count"] == 0

    def test_regression_xkdr_api_query_filters(self, monkeypatch):
        """
        Regression Test 3:
        Verifies that ingest_xkdr_air_quality queries /v1/measurements with:
        source=cpcb_caaqm, city=Pune, start=2023-01-11, end=2023-01-18, parameter=PM2.5,
        parameter=PM10, agg=raw, and all discovered station IDs.
        """
        captured_calls = []

        class MockResponse:
            def __init__(self, data):
                self._data = data
                self.status_code = 200
            def json(self):
                return {"data": self._data}
            def raise_for_status(self):
                pass

        def mock_get(url, *args, **kwargs):
            params = kwargs.get("params", [])
            captured_calls.append((url, params))
            if "stations" in url:
                return MockResponse([
                    {"station_id": "site_5409", "station_name": "Shivajinagar - IITM",
                     "city_name": "Pune", "state_name": "Maharashtra", "source": "cpcb_caaqm"},
                    {"station_id": "site_5408", "station_name": "Nigdi - IITM",
                     "city_name": "Pune", "state_name": "Maharashtra", "source": "cpcb_caaqm"},
                ])
            elif "measurements" in url:
                return MockResponse([])
            raise ValueError(url)

        import requests
        monkeypatch.setattr(requests, "get", mock_get)

        res = ingest_xkdr_air_quality(api_key="mock_key")

        meas_call = [c for c in captured_calls if "measurements" in c[0]][0]
        params_dict = {}
        for k, v in meas_call[1]:
            params_dict.setdefault(k, []).append(v)

        assert params_dict["source"] == ["cpcb_caaqm"]
        assert params_dict["city"] == ["Pune"]
        assert params_dict["start"] == ["2023-01-11"]
        assert params_dict["end"] == ["2023-01-18"]
        assert "PM2.5" in params_dict["parameter"]
        assert "PM10" in params_dict["parameter"]
        assert params_dict["agg"] == ["raw"]
        assert "site_5409" in params_dict["station"]
        assert "site_5408" in params_dict["station"]

    def test_regression_observations_outside_date_window_rejected(self, monkeypatch):
        """
        Regression Test 4:
        Verifies that observations with timestamps outside Jan 11–18, 2023 are rejected.
        """
        class MockResponse:
            def __init__(self, data):
                self._data = data
                self.status_code = 200
            def json(self):
                return {"data": self._data}
            def raise_for_status(self):
                pass

        def mock_get(url, *args, **kwargs):
            if "stations" in url:
                return MockResponse([{
                    "station_id": "site_5409",
                    "station_name": "Shivajinagar - IITM",
                    "city_name": "Pune",
                    "state_name": "Maharashtra",
                    "source": "cpcb_caaqm",
                }])
            elif "measurements" in url:
                return MockResponse([
                    # Timestamp from Jan 10 (before start)
                    {"station_id": "site_5409", "parameter_name": "PM2.5",
                     "collected_at": "2023-01-10T23:59:59", "value": 50.0},
                    # Timestamp from Jan 19 (after end)
                    {"station_id": "site_5409", "parameter_name": "PM2.5",
                     "collected_at": "2023-01-19T00:00:01", "value": 55.0},
                ])
            raise ValueError(url)

        import requests
        monkeypatch.setattr(requests, "get", mock_get)

        res = ingest_xkdr_air_quality(api_key="mock_key")
        assert res["status"] == "empty_period"
        assert res["observations_count"] == 0


class TestCamsGlobalPm25:
    """
    Tests for CAMS Global Atmospheric Composition Forecasts ingestion and validation.
    All tests use mock HTTP responses — no live API calls.
    """

    def _make_mock_response(self, n_hours: int = 192, include_nulls: bool = False,
                             include_negatives: bool = False, duplicate_ts: bool = False):
        """Helper: builds a mock Open-Meteo CAMS Global API response dict."""
        start = pd.Timestamp("2023-01-11 00:00", tz="Asia/Kolkata")
        timestamps = [
            (start + pd.Timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M")
            for i in range(n_hours)
        ]
        if duplicate_ts:
            timestamps[-1] = timestamps[-2]  # force duplicate

        pm25_values = [float(30 + i % 50) for i in range(n_hours)]
        if include_nulls:
            pm25_values[5] = None
        if include_negatives:
            pm25_values[10] = -1.0

        return {
            "latitude": 18.5,
            "longitude": 73.9,
            "timezone": "Asia/Kolkata",
            "elevation": 561.0,
            "hourly": {
                "time": timestamps,
                "pm2_5": pm25_values,
            }
        }

    def test_cams_192_hour_target_parsing(self, monkeypatch, tmp_path):
        """Verifies that a complete 192-hour CAMS series is parsed and saved correctly."""
        import requests
        mock_data = self._make_mock_response(192)

        class MockResp:
            status_code = 200
            def json(self): return mock_data
            def raise_for_status(self): pass

        monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResp())

        res = ingest_cams_global_pm25(
            output_dir=str(tmp_path / "raw"),
            processed_dir=str(tmp_path / "processed"),
        )
        assert res["status"] == "success"
        assert res["record_count"] == 192
        assert res["non_null_pm25"] == 192
        assert res["null_pm25"] == 0
        assert res["duplicate_count"] == 0
        assert res["pm25_min"] >= 0
        assert res["pm25_max"] is not None
        assert (tmp_path / "processed" / "cams_global_pune_pm25_hourly.parquet").exists()

    def test_cams_timezone_correctness(self, monkeypatch, tmp_path):
        """Verifies that timestamps in the cleaned parquet are timezone-aware Asia/Kolkata."""
        import requests
        mock_data = self._make_mock_response(192)

        class MockResp:
            status_code = 200
            def json(self): return mock_data
            def raise_for_status(self): pass

        monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResp())

        res = ingest_cams_global_pm25(
            output_dir=str(tmp_path / "raw"),
            processed_dir=str(tmp_path / "processed"),
        )
        assert res["status"] == "success"
        df = pd.read_parquet(tmp_path / "processed" / "cams_global_pune_pm25_hourly.parquet")
        assert str(df["timestamp"].dt.tz) in ["Asia/Kolkata", "+05:30"]
        assert df["timestamp"].iloc[0].hour == 0
        assert str(df["timestamp"].iloc[0].date()) == "2023-01-11"
        assert str(df["timestamp"].iloc[-1].date()) == "2023-01-18"

    def test_cams_duplicate_timestamp_rejection(self, monkeypatch, tmp_path):
        """Verifies that a series with duplicate timestamps fails validation."""
        import requests
        mock_data = self._make_mock_response(192, duplicate_ts=True)

        class MockResp:
            status_code = 200
            def json(self): return mock_data
            def raise_for_status(self): pass

        monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResp())

        res = ingest_cams_global_pm25(
            output_dir=str(tmp_path / "raw"),
            processed_dir=str(tmp_path / "processed"),
        )
        assert res["status"] == "validation_failed"
        assert res["duplicate_count"] > 0
        assert not (tmp_path / "processed" / "cams_global_pune_pm25_hourly.parquet").exists()

    def test_cams_negative_value_rejection(self, monkeypatch, tmp_path):
        """Verifies that a series with negative PM2.5 values fails validation."""
        import requests
        mock_data = self._make_mock_response(192, include_negatives=True)

        class MockResp:
            status_code = 200
            def json(self): return mock_data
            def raise_for_status(self): pass

        monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResp())

        res = ingest_cams_global_pm25(
            output_dir=str(tmp_path / "raw"),
            processed_dir=str(tmp_path / "processed"),
        )
        assert res["status"] == "validation_failed"
        assert "negative" in res["message"].lower()

    def test_cams_missing_value_rejection(self, monkeypatch, tmp_path):
        """Verifies that null PM2.5 values cause validation failure."""
        import requests
        mock_data = self._make_mock_response(192, include_nulls=True)

        class MockResp:
            status_code = 200
            def json(self): return mock_data
            def raise_for_status(self): pass

        monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResp())

        res = ingest_cams_global_pm25(
            output_dir=str(tmp_path / "raw"),
            processed_dir=str(tmp_path / "processed"),
        )
        assert res["status"] == "validation_failed"
        assert res["null_pm25"] > 0

    def test_cams_source_metadata_labeling(self, monkeypatch, tmp_path):
        """
        Verifies that the cleaned parquet contains correct source and source_type fields.
        source must be 'CAMS Global Atmospheric Composition Forecasts'.
        source_type must be 'modeled'.
        """
        import requests
        mock_data = self._make_mock_response(192)

        class MockResp:
            status_code = 200
            def json(self): return mock_data
            def raise_for_status(self): pass

        monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResp())

        res = ingest_cams_global_pm25(
            output_dir=str(tmp_path / "raw"),
            processed_dir=str(tmp_path / "processed"),
        )
        assert res["status"] == "success"
        assert res["source"] == "CAMS Global Atmospheric Composition Forecasts"
        assert res["source_type"] == "modeled"

        df = pd.read_parquet(tmp_path / "processed" / "cams_global_pune_pm25_hourly.parquet")
        assert (df["source"] == "CAMS Global Atmospheric Composition Forecasts").all()
        assert (df["source_type"] == "modeled").all()

    def test_cams_modeled_vs_observed_labeling_in_unified_features(self, tmp_path):
        """
        Verifies that when CAMS modeled PM2.5 is passed to build_unified_features,
        the output contains pm25_source_type='modeled' and that the result report
        explicitly labels this as modeled — not CPCB observed.
        """
        # Build minimal CAMS-style DataFrame (hourly, 8 hours for speed)
        ts_range = pd.date_range("2023-01-11 00:00", periods=8, freq="1h", tz="Asia/Kolkata")
        cams_df = pd.DataFrame({
            "timestamp": ts_range,
            "pm25": [50.0 + i for i in range(8)],
            "latitude": 18.5,
            "longitude": 73.9,
            "source": "CAMS Global Atmospheric Composition Forecasts",
            "source_type": "modeled",
        })

        mock_weather = pd.DataFrame([{
            "timestamp": ts,
            "temperature": 22.0, "humidity": 55.0,
            "wind_speed": 10.0, "rainfall": 0.0,
        } for ts in ts_range])

        mock_traffic = pd.DataFrame([{
            "timestamp": ts,
            "junction": "AlankarChowk", "camera_id": "a2",
            "session_file": "a2_11.csv", "direction": "UP",
            "car_raw": 10, "motorbike_raw": 5, "bus_raw": 1, "truck_raw": 0,
            "delta_car": 2, "delta_motorbike": 1, "delta_bus": 0, "delta_truck": 0,
            "traffic_count": 3,
        } for ts in ts_range])

        report = build_unified_features(
            traffic_df=mock_traffic,
            weather_df=mock_weather,
            aq_df=cams_df,
            output_dir=str(tmp_path),
        )

        assert report["status"] == "success"
        assert report["pm25_source_type"] == "modeled"
        assert "CAMS" in report["pm25_source"]

        feat_df = pd.read_parquet(tmp_path / "aeris_features.parquet")
        # pm25_source_type must be 'modeled' throughout
        assert (feat_df["pm25_source_type"] == "modeled").all()
        # pm25 column must not contain CPCB labeling
        assert "cpcb" not in feat_df["pm25_source"].str.lower().iloc[0]

    def test_gating_still_blocks_when_no_pm25_available(self, tmp_path):
        """
        Verifies that the updated gating logic still blocks when no PM2.5 at all
        is available (neither observed nor modeled).
        """
        mock_weather = pd.DataFrame([{
            "timestamp": pd.Timestamp("2023-01-11 09:00:00+05:30"),
            "temperature": 22.0, "humidity": 50.0,
            "wind_speed": 10.0, "rainfall": 0.0,
        }])
        empty_aq = pd.DataFrame(columns=["timestamp", "pm25", "pm10"])
        report = build_unified_features(
            weather_df=mock_weather,
            aq_df=empty_aq,
            output_dir=str(tmp_path),
        )
        assert report["status"] == "gated_missing_air_quality"
        assert report["aeris_features_path"] is None


class TestMlFeatureBuilder:
    """Tests for build_ml_features: no-leakage policy, time-based split, feature columns."""

    def _make_cams_unified(self, n_hours: int = 48) -> pd.DataFrame:
        """Build a minimal unified DataFrame resembling CAMS-based aeris_features.parquet."""
        ts_range = pd.date_range(
            "2023-01-11 00:00", periods=n_hours, freq="1h", tz="Asia/Kolkata"
        )
        rows = []
        for ts in ts_range:
            for zone_id in ["PUNE_ALANKAR_CHOWK", "PUNE_RTO_CHOWK"]:
                rows.append({
                    "timestamp": ts,
                    "zone_id": zone_id,
                    "latitude": 18.52,
                    "longitude": 73.87,
                    "pm25": float(50 + ts.hour % 20),
                    "pm10": np.nan,
                    "temperature": 22.0,
                    "humidity": 55.0,
                    "wind_speed": 10.0,
                    "rainfall": 0.0,
                    "traffic_count": float(ts.hour * 5),
                    "pm25_source": "CAMS Global Atmospheric Composition Forecasts",
                    "pm25_source_type": "modeled",
                })
        return pd.DataFrame(rows)

    def test_no_future_pm25_leakage_in_features(self, tmp_path):
        """
        Critical: Verifies that PM2.5 lag and rolling features at prediction time t
        use ONLY PM2.5 from t-1 or earlier.
        The feature at time index 0 (lag_1h) must be NaN (no prior data available).
        The feature at time index 1 (lag_1h) must equal PM2.5 at index 0 (previous hour).
        """
        unified = self._make_cams_unified(n_hours=48)
        res = build_ml_features(unified, val_hours=8, output_dir=str(tmp_path))

        assert "train_path" in res and res["train_path"] is not None
        train_df = pd.read_parquet(res["train_path"])

        # Sort to get deterministic order for one zone
        zone_df = (
            train_df[train_df["zone_id"] == "PUNE_ALANKAR_CHOWK"]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        # At t=0: pm25_lag_1h must be NaN (no prior PM2.5 exists)
        assert pd.isna(zone_df["pm25_lag_1h"].iloc[0]), (
            "pm25_lag_1h at t=0 must be NaN — no prior PM2.5 is available."
        )
        # At t=1: pm25_lag_1h must equal pm25 at t=0
        assert zone_df["pm25_lag_1h"].iloc[1] == zone_df["pm25"].iloc[0], (
            "pm25_lag_1h at t=1 must equal pm25 at t=0 (previous hour)."
        )

    def test_time_based_split_not_random(self, tmp_path):
        """
        Verifies that the validation split contains only the most recent val_hours timestamps,
        not a random subset.
        """
        unified = self._make_cams_unified(n_hours=48)
        res = build_ml_features(unified, val_hours=8, output_dir=str(tmp_path))

        train_df = pd.read_parquet(res["train_path"])
        val_df = pd.read_parquet(res["val_path"])

        train_max_ts = train_df["timestamp"].max()
        val_min_ts = val_df["timestamp"].min()
        # All validation timestamps must come AFTER all training timestamps
        assert val_min_ts > train_max_ts, (
            "Validation timestamps must be strictly later than training timestamps."
        )
        assert res["val_hours"] == 8

    def test_pm25_target_never_in_feature_columns(self, tmp_path):
        """
        Verifies that 'pm25' (the prediction target) is never listed as a feature column.
        Only pm25_lag_Nh and pm25_roll_* features are permitted.
        """
        unified = self._make_cams_unified(n_hours=48)
        res = build_ml_features(unified, val_hours=8, output_dir=str(tmp_path))

        feature_cols = res["feature_columns"]
        assert "pm25" not in feature_cols, (
            "'pm25' (target) must never appear in feature_columns."
        )
        assert "pm10" not in feature_cols, (
            "'pm10' must not appear in feature_columns."
        )
        # Lag features must be present
        assert "pm25_lag_1h" in feature_cols
        assert "pm25_lag_24h" in feature_cols

    def test_modeled_source_type_preserved_in_ml_output(self, tmp_path):
        """Verifies that pm25_source_type='modeled' is preserved in train/val splits."""
        unified = self._make_cams_unified(n_hours=48)
        res = build_ml_features(unified, val_hours=8, output_dir=str(tmp_path))

        assert res["pm25_source_type"] == "modeled"
        val_df = pd.read_parquet(res["val_path"])
        assert (val_df["pm25_source_type"] == "modeled").all()


class TestCityLevelForecastingDataset:
    """
    Task 6 Regression Tests for the dedicated city-level hourly ML forecasting dataset.
    Validates:
    1. Exactly one ML row per timestamp
    2. No duplicate timestamps
    3. Target is t+1 relative to feature timestamp
    4. Current-hour traffic/weather are allowed
    5. No future PM2.5 appears in features
    6. PM2.5 lag_1h is strictly earlier than target time
    7. Chronological train/validation split (no random shuffling)
    8. Persistence baseline calculation
    9. No null target rows
    10. No PM10 fabrication
    """

    @pytest.fixture
    def mock_city_inputs(self):
        """Creates a deterministic 192-hour mock dataset for Pune (Jan 11-18, 2023)."""
        ts_range = pd.date_range("2023-01-11 00:00", periods=192, freq="1h", tz="Asia/Kolkata")

        # Weather: 192 rows
        weather_df = pd.DataFrame({
            "timestamp": ts_range,
            "temperature": 15.0 + 10.0 * np.sin(np.arange(192) * 2 * np.pi / 24),
            "humidity": 50.0 + 20.0 * np.cos(np.arange(192) * 2 * np.pi / 24),
            "wind_speed": 8.0 + 4.0 * np.sin(np.arange(192) * 2 * np.pi / 12),
            "rainfall": np.zeros(192),
        })

        # CAMS PM2.5: 192 rows
        pm25_vals = 30.0 + 20.0 * np.sin(np.arange(192) * 2 * np.pi / 24) + np.arange(192) * 0.1
        cams_df = pd.DataFrame({
            "timestamp": ts_range,
            "pm25": pm25_vals,
            "latitude": 18.5,
            "longitude": 73.9,
            "source": "CAMS Global Atmospheric Composition Forecasts",
            "source_type": "modeled",
        })

        # Traffic: 3 junctions across the 192 hours
        traffic_records = []
        for j in ["AlankarChowk", "JehangirChowk", "RTOChowk"]:
            for ts in ts_range:
                # Active only during morning hours 9-12
                cnt = float(100 + ts.hour * 10) if 9 <= ts.hour <= 12 else 0.0
                traffic_records.append({
                    "timestamp": ts,
                    "junction": j,
                    "traffic_count": cnt,
                })
        traffic_df = pd.DataFrame(traffic_records)

        return traffic_df, weather_df, cams_df

    def test_city_ml_exactly_one_row_per_timestamp(self, mock_city_inputs, tmp_path):
        """Regression Test 1: City-level dataset contains exactly ONE row per hourly timestamp."""
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        city_df = pd.read_parquet(res["city_parquet_path"])
        assert len(city_df) == 192
        assert len(city_df) == city_df["timestamp"].nunique()

    def test_city_ml_no_duplicate_timestamps(self, mock_city_inputs, tmp_path):
        """Regression Test 2: City-level dataset has strictly zero duplicate timestamps."""
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        city_df = pd.read_parquet(res["city_parquet_path"])
        assert not city_df["timestamp"].duplicated().any()

    def test_city_ml_target_is_t_plus_1(self, mock_city_inputs, tmp_path):
        """Regression Test 3: Target pm25_target_t_plus_1 is strictly PM2.5 at hour t+1."""
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        city_df = pd.read_parquet(res["city_parquet_path"])
        cams_pm25 = cams_df.sort_values("timestamp")["pm25"].values

        # For every row i < 191, target at row i must equal cams_pm25 at row i+1
        for i in range(191):
            assert city_df[CITY_TARGET_COLUMN].iloc[i] == cams_pm25[i + 1]

        # Row 191 (last hour) target is NaN
        assert pd.isna(city_df[CITY_TARGET_COLUMN].iloc[191])

    def test_city_ml_current_hour_traffic_weather_allowed(self, mock_city_inputs, tmp_path):
        """Regression Test 4: Current-hour traffic and weather features correspond to timestamp t."""
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        city_df = pd.read_parquet(res["city_parquet_path"])
        weather_sorted = weather_df.sort_values("timestamp").reset_index(drop=True)

        # Temperature at row i matches weather temperature at row i
        for i in [0, 10, 50, 100, 150]:
            assert city_df["temperature"].iloc[i] == weather_sorted["temperature"].iloc[i]
            assert city_df["humidity"].iloc[i] == weather_sorted["humidity"].iloc[i]
            assert city_df["wind_speed"].iloc[i] == weather_sorted["wind_speed"].iloc[i]
            assert city_df["rainfall"].iloc[i] == weather_sorted["rainfall"].iloc[i]

    def test_city_ml_no_future_pm25_in_features(self, mock_city_inputs, tmp_path):
        """Regression Test 5: Features at timestamp t contain NO future PM2.5 (from t+1 or later)."""
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        assert CITY_TARGET_COLUMN not in CITY_FEATURE_COLUMNS
        assert "pm25_target_t_plus_1" not in CITY_FEATURE_COLUMNS
        assert "pm25_target" not in CITY_FEATURE_COLUMNS
        assert "pm25_current" not in CITY_FEATURE_COLUMNS

        # Verify all feature columns
        for col in CITY_FEATURE_COLUMNS:
            assert "t_plus" not in col
            assert "future" not in col

    def test_city_ml_pm25_lag_1h_strictly_earlier_than_target(self, mock_city_inputs, tmp_path):
        """
        Regression Test 6:
        PM2.5 lag_1h represents PM2.5 at t-1, which is strictly 2 hours earlier than target time t+1,
        and 1 hour earlier than feature timestamp t.
        """
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        city_df = pd.read_parquet(res["city_parquet_path"])
        cams_pm25 = cams_df.sort_values("timestamp")["pm25"].values

        # At row 0: lag_1h is NaN (no prior observation)
        assert pd.isna(city_df["pm25_lag_1h"].iloc[0])

        # At row i >= 1: lag_1h equals cams_pm25 at row i-1
        for i in range(1, 20):
            assert city_df["pm25_lag_1h"].iloc[i] == cams_pm25[i - 1]
            # Target at row i is cams_pm25 at row i+1
            target_val = city_df[CITY_TARGET_COLUMN].iloc[i]
            # Target time index is i+1, lag_1h index is i-1; difference is exactly 2 hours
            assert cams_pm25[i + 1] == target_val

    def test_city_ml_chronological_train_val_split(self, mock_city_inputs, tmp_path):
        """Regression Test 7: Train and validation splits are strictly partitioned chronologically."""
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        train_df = pd.read_parquet(res["train_path"])
        val_df = pd.read_parquet(res["val_path"])

        # Train must be strictly before 2023-01-18
        assert (train_df["timestamp"] < "2023-01-18").all()

        # Val must be on or after 2023-01-18
        assert (val_df["timestamp"] >= "2023-01-18").all()

        # Strict chronological separation: max train timestamp < min val timestamp
        assert train_df["timestamp"].max() < val_df["timestamp"].min()

        # Exact row counts:
        # Train has 144 hours (Jan 12 00:00 to Jan 17 23:00, after 24h lag requirement)
        # Val has 23 hours (Jan 18 00:00 to Jan 18 22:00, excluding last hour which has no t+1)
        assert len(train_df) == 144
        assert len(val_df) == 23

    def test_city_ml_persistence_baseline_calculation(self):
        """
        Regression Test 8:
        Validates calculate_persistence_baseline on synthetic actual vs predicted series.
        """
        actual = [50.0, 60.0, 70.0]
        predicted = [48.0, 62.0, 70.0]
        # Diff: [2.0, -2.0, 0.0]
        # Abs: [2.0, 2.0, 0.0] -> MAE = 4.0 / 3 = 1.3333
        # Sq:  [4.0, 4.0, 0.0] -> MSE = 8.0 / 3 = 2.6667 -> RMSE = 1.6330
        res = calculate_persistence_baseline(actual, predicted)
        assert res["mae"] == round(4.0 / 3.0, 4)
        assert res["rmse"] == round(math.sqrt(8.0 / 3.0), 4)

    def test_city_ml_no_null_target_rows(self, mock_city_inputs, tmp_path):
        """Regression Test 9: Neither train nor validation splits contain any null target values."""
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        train_df = pd.read_parquet(res["train_path"])
        val_df = pd.read_parquet(res["val_path"])

        assert train_df[CITY_TARGET_COLUMN].isna().sum() == 0
        assert val_df[CITY_TARGET_COLUMN].isna().sum() == 0

        # Also verify zero nulls across all feature columns
        assert train_df[CITY_FEATURE_COLUMNS].isna().sum().sum() == 0
        assert val_df[CITY_FEATURE_COLUMNS].isna().sum().sum() == 0

    def test_city_ml_no_pm10_fabrication(self, mock_city_inputs, tmp_path):
        """Regression Test 10: PM10 is not fabricated or injected as a predictor into the city ML dataset."""
        traffic_df, weather_df, cams_df = mock_city_inputs
        res = build_city_level_ml_dataset(
            traffic_df=traffic_df,
            weather_df=weather_df,
            cams_df=cams_df,
            output_dir=str(tmp_path),
        )
        assert "pm10" not in CITY_FEATURE_COLUMNS
        assert not any("pm10" in col.lower() for col in CITY_FEATURE_COLUMNS)

        city_df = pd.read_parquet(res["city_parquet_path"])
        assert "pm10" not in city_df.columns
