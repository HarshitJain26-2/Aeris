"""
Driver Service (backend/app/services/driver_service.py)
-------------------------------------------------------
Computes model feature attribution from SHAP importance artifact:
ml/evaluation/shap_importance.csv

SCIENTIFIC SEMANTICS:
- Percentages represent normalized mean absolute SHAP feature-attribution shares.
- They are NOT physical emission-source apportionment and do NOT prove causal fraction.
- Four deterministic groups:
    1. Recent PM2.5 history (10 lag & rolling features)
    2. Weather (4 meteorological predictors)
    3. Traffic (8 traffic sensor & interaction features)
    4. Time / calendar (3 temporal features)
- Rounding: each group rounded to 2 decimal places, with deterministic final-adjustment
  on the largest group only if necessary to ensure exact 100.00% sum.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional

from backend.app.schemas.drivers import (
    DriverAttribution,
    DriverAttributionResponse,
    DriverCategory,
)

logger = logging.getLogger("aeris.driver_service")

DEFAULT_SHAP_PATH = "ml/evaluation/shap_importance.csv"

DRIVER_GROUPS: Dict[DriverCategory, List[str]] = {
    "Recent PM2.5 history": [
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
    ],
    "Weather": [
        "temperature",
        "humidity",
        "wind_speed",
        "rainfall",
    ],
    "Traffic": [
        "traffic_alankar",
        "traffic_jehangir",
        "traffic_rto",
        "traffic_total",
        "traffic_roll_mean_3h",
        "traffic_roll_mean_6h",
        "traffic_x_wind",
        "traffic_x_humidity",
    ],
    "Time / calendar": [
        "hour_of_day",
        "day_of_week",
        "is_weekend",
    ],
}

DRIVER_DESCRIPTIONS: Dict[DriverCategory, str] = {
    "Recent PM2.5 history": (
        "Normalized contribution of recent PM2.5 lag and rolling-history features to "
        "model prediction variation, based on mean absolute SHAP values."
    ),
    "Weather": (
        "Normalized contribution of meteorological predictors to "
        "model prediction variation, based on mean absolute SHAP values."
    ),
    "Traffic": (
        "Normalized contribution of traffic and traffic-weather interaction predictors to "
        "model prediction variation, based on mean absolute SHAP values."
    ),
    "Time / calendar": (
        "Normalized contribution of temporal/calendar predictors to "
        "model prediction variation, based on mean absolute SHAP values."
    ),
}

DISCLAIMER_TEXT = (
    "Model feature attribution derived from mean absolute SHAP values. "
    "These percentages describe model behavior and are not physical emission-source "
    "apportionment or causal proof."
)


class DriverService:
    """Service for computing real model-driver attribution from SHAP importance artifact."""

    def __init__(self, shap_path: str = DEFAULT_SHAP_PATH):
        self._shap_path = Path(shap_path)

    def _resolve_shap_path(self) -> Path:
        candidate_paths = [
            self._shap_path,
            Path(__file__).resolve().parent.parent.parent.parent / self._shap_path,
        ]
        for p in candidate_paths:
            if p.exists():
                return p
        raise FileNotFoundError(
            f"SHAP importance artifact not found at {self._shap_path}. "
            f"Ensure {DEFAULT_SHAP_PATH} exists."
        )

    def load_shap_feature_importance(self, target_path: Optional[Path] = None) -> Dict[str, float]:
        path = target_path or self._resolve_shap_path()
        shap_values: Dict[str, float] = {}
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                feat = row.get("feature", "").strip()
                val_str = row.get("mean_abs_shap", "0.0").strip()
                if feat:
                    shap_values[feat] = float(val_str)
        return shap_values

    def compute_attribution(
        self, shap_values: Optional[Dict[str, float]] = None
    ) -> DriverAttributionResponse:
        if shap_values is None:
            shap_values = self.load_shap_feature_importance()

        group_sums: Dict[DriverCategory, float] = {}
        for category, features in DRIVER_GROUPS.items():
            group_sums[category] = sum(shap_values.get(f, 0.0) for f in features)

        total_shap = sum(group_sums.values())
        if total_shap <= 0.0:
            raise ValueError("Total mean absolute SHAP value across groups must be positive.")

        # Compute raw percentages
        raw_pcts = {
            category: (group_sum / total_shap) * 100.0
            for category, group_sum in group_sums.items()
        }

        # Round to 2 decimal places
        rounded_pcts = {
            category: round(pct, 2)
            for category, pct in raw_pcts.items()
        }

        # Deterministic adjustment on largest group only if necessary due to rounding
        current_sum = round(sum(rounded_pcts.values()), 2)
        diff = round(100.0 - current_sum, 2)
        if abs(diff) > 1e-6:
            largest_category = max(
                rounded_pcts.keys(),
                key=lambda k: (rounded_pcts[k], k),
            )
            rounded_pcts[largest_category] = round(rounded_pcts[largest_category] + diff, 2)

        driver_items: List[DriverAttribution] = []
        for category in DRIVER_GROUPS.keys():
            pct = rounded_pcts[category]
            driver_items.append(
                DriverAttribution(
                    category=category,
                    estimatedPct=pct,
                    ciLower=pct,
                    ciUpper=pct,
                    description=DRIVER_DESCRIPTIONS[category],
                )
            )

        return DriverAttributionResponse(
            city="Pune",
            period="validation holdout — model feature attribution",
            drivers=driver_items,
            method="model_feature_attribution",
            disclaimer=DISCLAIMER_TEXT,
            dataSource="model_estimate",
        )
