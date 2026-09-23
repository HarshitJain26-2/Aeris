"""
Unit and Integration Tests for AERIS Data/ML Pipeline (tests/test_data_pipeline.py)
===================================================================================
Tests core pipeline invariants:
1. Timestamp parsing & timezone localization
2. Traffic session-aware delta computation and counter reset handling
3. Camera-level and direction-level preservation
4. Weather physical range clipping
5. OpenAQ API key detection & graceful missing-key blocking
6. Haversine distance spatial mapping threshold
7. Strict gating of aeris_features.parquet when real AQ data is absent
8. Schema validation and duplicate detection
"""

import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.src.clean import clean_air_quality_data, clean_traffic_data, clean_weather_data
from ml.src.features import (
    AIR_QUALITY_DISTANCE_THRESHOLD_KM,
    ZONE_COORDINATES,
    build_hourly_traffic_features,
    build_unified_features,
    build_zone_traffic_summary,
    haversine_distance_km,
    map_air_quality_to_zones,
)
from ml.src.ingest import ingest_openaq


class TestTimestampAndCleaning:
    def test_weather_cleaning_and_range_validation(self):
        """Validates that weather values outside physical bounds are clipped and timezone is applied."""
        mock_raw = {
            "hourly": {
                "time": ["2023-01-11T09:00", "2023-01-11T10:00"],
                "temperature_2m": [25.0, 75.0],  # 75 is invalid, should be clipped to 60
                "relative_humidity_2m": [50.0, -10.0],  # -10 invalid, clipped to 0
                "wind_speed_10m": [12.0, 250.0],  # 250 clipped to 200
                "precipitation": [0.0, -2.0],  # -2 clipped to 0
            }
        }
        clean_df, audit = clean_weather_data(mock_raw)
        assert len(clean_df) == 2
        assert clean_df["temperature"].iloc[1] == 60.0
        assert clean_df["humidity"].iloc[1] == 0.0
        assert clean_df["wind_speed"].iloc[1] == 200.0
        assert clean_df["rainfall"].iloc[1] == 0.0
        assert clean_df["timestamp"].dt.tz.zone == "Asia/Kolkata" or str(clean_df["timestamp"].dt.tz) == "+05:30"
        assert audit["range_violations_corrected"] > 0

    def test_traffic_session_aware_deltas(self):
        """Tests that cumulative counters are accurately converted to non-negative step deltas per session."""
        mock_traffic = pd.DataFrame([
            {"date": "2023-01-11", "Time": "09:00:00", "Direction": "UP", "car": 0, "motorbike": 0, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv", "is_continuation": False},
            {"date": "2023-01-11", "Time": "09:00:01", "Direction": "UP", "car": 1, "motorbike": 2, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv", "is_continuation": False},
            {"date": "2023-01-11", "Time": "09:00:02", "Direction": "UP", "car": 3, "motorbike": 5, "bus": 1, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv", "is_continuation": False},
            # Continuation file resets to 0
            {"date": "2023-01-11", "Time": "11:26:00", "Direction": "UP", "car": 0, "motorbike": 0, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11_one.csv", "is_continuation": True},
            {"date": "2023-01-11", "Time": "11:26:01", "Direction": "UP", "car": 2, "motorbike": 1, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11_one.csv", "is_continuation": True},
        ])

        clean_df, audit = clean_traffic_data(mock_traffic)
        assert audit["final_valid_rows"] == 5
        # Total vehicles should be (1+2) + (2+3+1) + (0) + (2+1) = 3 + 6 + 0 + 3 = 12
        assert audit["total_vehicles_counted"] == 12.0
        assert (clean_df["traffic_count"] >= 0).all()
        # Verify camera and direction fields are preserved
        assert "camera_id" in clean_df.columns
        assert "direction" in clean_df.columns

    def test_traffic_invalid_timestamp_handling(self):
        """Verifies that unparseable timestamps or directions are dropped with audit records."""
        bad_traffic = pd.DataFrame([
            {"date": "2023-01-11", "Time": "invalid_time", "Direction": "UP", "car": 1, "motorbike": 0, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv", "is_continuation": False},
            {"date": "2023-01-11", "Time": "09:00:00", "Direction": "INVALID_DIR", "car": 1, "motorbike": 0, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv", "is_continuation": False},
            {"date": "2023-01-11", "Time": "09:00:01", "Direction": "UP", "car": 1, "motorbike": 0, "bus": 0, "truck": 0,
             "junction": "AlankarChowk", "camera_id": "a2", "session_file": "a2_11.csv", "is_continuation": False},
        ])
        clean_df, audit = clean_traffic_data(bad_traffic)
        assert len(clean_df) == 1
        assert audit["final_valid_rows"] == 1


class TestSpatialAndGating:
    def test_haversine_distance(self):
        """Verifies Haversine formula against known Pune coordinates."""
        # Shivajinagar to RTO Chowk (~2.1 km)
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

        # Case 1: Empty air quality dataframe
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
        # But intermediate tables must exist
        assert (tmp_path / "traffic_clean.parquet").exists()
        assert (tmp_path / "traffic_hourly.parquet").exists()
        assert (tmp_path / "weather_hourly.parquet").exists()

    def test_openaq_missing_key_graceful_block(self):
        """Verifies that ingest_openaq safely detects missing key and blocks execution without raising unhandled errors."""
        res = ingest_openaq(api_key=None)
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
            "wind_speed", "rainfall", "traffic_count"
        ]
        assert list(res_df.columns) == expected_schema
        # Check no duplicate (timestamp, zone_id) keys
        assert not res_df.duplicated(subset=["timestamp", "zone_id"]).any()
