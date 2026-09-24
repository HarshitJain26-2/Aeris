"""
India National AQI (CPCB) Calculation Utilities
Conforms to CPCB Breakpoints and matches frontend/src/lib/cpcbAqi.ts
"""
from typing import Dict, List, Optional


CPCB_BANDS: List[Dict[str, any]] = [
    {
        "band": "Good",
        "aqi_min": 0,
        "aqi_max": 50,
        "pm25_min": 0.0,
        "pm25_max": 30.0,
    },
    {
        "band": "Satisfactory",
        "aqi_min": 51,
        "aqi_max": 100,
        "pm25_min": 31.0,
        "pm25_max": 60.0,
    },
    {
        "band": "Moderate",
        "aqi_min": 101,
        "aqi_max": 200,
        "pm25_min": 61.0,
        "pm25_max": 90.0,
    },
    {
        "band": "Poor",
        "aqi_min": 201,
        "aqi_max": 300,
        "pm25_min": 91.0,
        "pm25_max": 120.0,
    },
    {
        "band": "Very Poor",
        "aqi_min": 301,
        "aqi_max": 400,
        "pm25_min": 121.0,
        "pm25_max": 250.0,
    },
    {
        "band": "Severe",
        "aqi_min": 401,
        "aqi_max": 500,
        "pm25_min": 251.0,
        "pm25_max": 999.0,
    },
]


def get_band_from_pm25(pm25: float) -> str:
    """Returns CPCB band string from PM2.5 concentration."""
    for b in CPCB_BANDS:
        if b["pm25_min"] <= pm25 <= b["pm25_max"]:
            return b["band"]
    if pm25 > 250.0:
        return "Severe"
    return "Good"


def get_band_from_aqi(aqi: int) -> str:
    """Returns CPCB band string from CPCB AQI value."""
    for b in CPCB_BANDS:
        if b["aqi_min"] <= aqi <= b["aqi_max"]:
            return b["band"]
    if aqi > 500:
        return "Severe"
    return "Good"


def estimate_aqi_from_pm25(pm25: float) -> int:
    """
    Approximate AQI from PM2.5 using CPCB linear sub-index formula.
    Identical in behavior to frontend/src/lib/cpcbAqi.ts estimateAqiFromPm25.
    """
    if pm25 < 0:
        pm25 = 0.0

    matched_band: Optional[Dict[str, any]] = None
    for b in CPCB_BANDS:
        if b["pm25_min"] <= pm25 <= b["pm25_max"]:
            matched_band = b
            break

    if matched_band is None:
        if pm25 > 250.0:
            matched_band = CPCB_BANDS[-1]
        else:
            # Below 31 but not <= 30 due to float, or negative
            matched_band = CPCB_BANDS[0]

    pm_min = matched_band["pm25_min"]
    pm_max = matched_band["pm25_max"]
    aqi_min = matched_band["aqi_min"]
    aqi_max = matched_band["aqi_max"]

    if pm_max == pm_min:
        return aqi_min

    aqi = ((aqi_max - aqi_min) / (pm_max - pm_min)) * (pm25 - pm_min) + aqi_min
    return int(round(min(500.0, max(0.0, aqi))))
