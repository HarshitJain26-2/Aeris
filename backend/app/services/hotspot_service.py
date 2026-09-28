"""
Hotspot Service (backend/app/services/hotspot_service.py)
---------------------------------------------------------
Computes real model-estimated urban hotspot points for Pune across the 3 documented ML zones.

SCIENTIFIC PROVENANCE & SEMANTICS:
1. Modeled PM2.5 target is derived from CAMS Global Atmospheric Composition Forecasts.
   - It is city-wide modeled atmospheric PM2.5 concentration, NOT independent per-zone observations.
   - Values are strictly identical across the 3 zones (never fabricated per-zone differences).
   - Provenance is strictly labeled 'model_estimate' (never 'observed' or 'DEMO_FIXTURE').

2. Spatial Hotspot Intensity:
   - Derived from zone-level traffic_count at the latest common timestamp.
   - Min-max normalized across the 3 zones to [0, 1].
   - If all zone traffic counts are equal or zero, a safe fallback intensity of 0.5 is assigned.
   - Values are strictly clamped to [0, 1].

3. Dominant Driver:
   - Spatially, traffic is the only currently available zone-varying predictor in this hotspot construction.
   - We assign 'Traffic' as a contextual/model feature label.
   - NOTE: This is NOT physical emission-source apportionment or causal proof.
   - Industrial and Residential/Biomass percentages are strictly not invented or fabricated.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
import pandas as pd

from backend.app.repositories.zone_repository import ZoneRepository
from backend.app.schemas.current import CpcbBand
from backend.app.schemas.hotspots import (
    HotspotFeature,
    HotspotGeoJSON,
    HotspotMetadata,
    HotspotPointGeometry,
    HotspotProperties,
)
from backend.app.utils.cpcb_aqi import estimate_aqi_from_pm25, get_band_from_aqi

logger = logging.getLogger("aeris.hotspot_service")

DEFAULT_FEATURES_PATH = "data/processed/aeris_features.parquet"
IST = timezone(timedelta(hours=5, minutes=30))


class HotspotService:
    """Service providing real model-estimated urban environmental hotspots for Pune."""

    def __init__(
        self,
        features_path: Optional[Union[str, Path]] = None,
        zone_repo: Optional[ZoneRepository] = None,
    ):
        self._features_path_str = str(features_path) if features_path else DEFAULT_FEATURES_PATH
        self._zone_repo = zone_repo or ZoneRepository()

    def _resolve_features_path(self) -> Path:
        """Resolves feature dataset path across project root or working directory."""
        path = Path(self._features_path_str)
        if path.is_absolute() and path.exists():
            return path

        candidate_paths = [
            path,
            Path(__file__).resolve().parent.parent.parent.parent / path,
            Path.cwd() / path,
        ]
        for candidate in candidate_paths:
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            f"Processed feature dataset not found at '{self._features_path_str}'."
        )

    def get_hotspots(self) -> HotspotGeoJSON:
        """
        Extracts the latest common modeled PM2.5 and zone-level traffic predictors
        to construct real contextual hotspot GeoJSON points for the 3 documented zones.
        """
        resolved_path = self._resolve_features_path()

        try:
            df = pd.read_parquet(resolved_path)
        except Exception as e:
            raise ValueError(f"Failed to read feature dataset: {e}")

        if df.empty:
            raise ValueError("Processed feature dataset is empty.")

        required_cols = {"timestamp", "zone_id", "pm25", "traffic_count"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Dataset is missing required columns: {missing_cols}")

        # Filter for valid modeled PM2.5
        if "pm25_source_type" in df.columns:
            valid_mask = df["pm25"].notna() & (
                df["pm25_source_type"].astype(str).str.lower() == "modeled"
            )
        else:
            valid_mask = df["pm25"].notna()

        valid_df = df[valid_mask]
        if valid_df.empty:
            raise ValueError("No valid modeled PM2.5 data exists in dataset.")

        # Documented ML junction zones
        documented_zones = self._zone_repo.list_zones()
        doc_zone_ids = [z.zone_id for z in documented_zones]

        # Select latest common timestamp containing all documented zones
        timestamps_with_doc_zones = (
            valid_df[valid_df["zone_id"].isin(doc_zone_ids)]
            .groupby("timestamp")["zone_id"]
            .nunique()
        )
        common_timestamps = timestamps_with_doc_zones[
            timestamps_with_doc_zones == len(doc_zone_ids)
        ].index

        if len(common_timestamps) == 0:
            raise ValueError(
                "No common timestamp contains valid modeled PM2.5 across all documented zones."
            )

        latest_ts = common_timestamps.max()

        df_latest = valid_df[valid_df["timestamp"] == latest_ts]
        if df_latest.empty:
            raise ValueError("No data found for the selected timestamp.")

        # Common city-wide modeled PM2.5 (CAMS Global atmospheric forecast)
        # Uniform across all 3 zones to preserve scientific truthfulness
        raw_pm25 = float(df_latest["pm25"].dropna().iloc[0])
        city_pm25 = round(raw_pm25, 2)

        # Compute India CPCB AQI and band
        aqi_val = estimate_aqi_from_pm25(city_pm25)
        aqi_band = CpcbBand(get_band_from_aqi(aqi_val))

        # Extract zone-level traffic counts
        zone_traffic: Dict[str, float] = {}
        for zone in documented_zones:
            zone_rows = df_latest[df_latest["zone_id"] == zone.zone_id]
            if not zone_rows.empty and pd.notna(zone_rows["traffic_count"].iloc[0]):
                zone_traffic[zone.zone_id] = float(zone_rows["traffic_count"].iloc[0])
            else:
                zone_traffic[zone.zone_id] = 0.0

        # Compute normalized spatial hotspot intensity (clamped to [0, 1])
        # If all traffic counts are equal or zero, fallback to safe 0.5 intensity
        traffic_values = [zone_traffic[z.zone_id] for z in documented_zones]
        min_traffic = min(traffic_values)
        max_traffic = max(traffic_values)

        intensities: Dict[str, float] = {}
        if max_traffic == min_traffic:
            for z in documented_zones:
                intensities[z.zone_id] = 0.5
        else:
            for z in documented_zones:
                t = zone_traffic[z.zone_id]
                normalized = (t - min_traffic) / (max_traffic - min_traffic)
                clamped = max(0.0, min(1.0, normalized))
                intensities[z.zone_id] = round(clamped, 2)

        # Dominant driver attribution:
        # Spatially, traffic is the only currently available zone-varying predictor
        # in this hotspot construction. We assign 'Traffic' as a contextual/model
        # feature label. This is NOT causal physical emission source apportionment,
        # and we strictly do not fabricate Industrial or Residential/Biomass percentages.
        dominant_driver = "Traffic"

        # Format ISO 8601 timezone-aware timestamp string
        if hasattr(latest_ts, "isoformat"):
            if getattr(latest_ts, "tzinfo", None) is None:
                generated_at = latest_ts.replace(tzinfo=IST).isoformat()
            else:
                generated_at = latest_ts.isoformat()
        else:
            generated_at = str(latest_ts)

        # Build exactly 3 hotspot GeoJSON features
        features: List[HotspotFeature] = []
        for zone in documented_zones:
            feature = HotspotFeature(
                geometry=HotspotPointGeometry(
                    coordinates=[round(zone.longitude, 4), round(zone.latitude, 4)]
                ),
                properties=HotspotProperties(
                    id=zone.zone_id,
                    name=zone.name,
                    locality=zone.name,
                    pm25=city_pm25,
                    aqi=aqi_val,
                    aqiBand=aqi_band,
                    dominantDriver=dominant_driver,
                    intensity=intensities[zone.zone_id],
                    dataSource="model_estimate",
                ),
            )
            features.append(feature)

        metadata = HotspotMetadata(
            city="Pune",
            generatedAt=generated_at,
            dataSource="model_estimate",
        )

        return HotspotGeoJSON(
            type="FeatureCollection",
            features=features,
            metadata=metadata,
        )
