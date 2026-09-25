"""
AERIS ML Inference Service (backend/app/services/inference_service.py)
=====================================================================
Bridges backend FastAPI requests to the ML inference layer (ml/src/inference.py).

Guarantees:
- Preserves canonical 25-feature schema ordering.
- Passes input_timestamp through to predict_next_hour().
- Does NOT duplicate ML inference or scenario logic.
"""

from pathlib import Path
import sys
from typing import Any, Dict

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ml.src.features import CITY_FEATURE_COLUMNS
from ml.src.inference import predict_next_hour


def run_forecast_service(request_data: Any) -> Dict[str, Any]:
    """
    Accepts validated request data, converts it to a dict preserving canonical
    25-feature ordering, passes input_timestamp, and calls predict_next_hour().

    Args:
        request_data: Validated ForecastRequest or dict containing features and input_timestamp.

    Returns:
        Dict reporting input_timestamp, forecast_timestamp, pm25_forecast,
        target_source, and target_source_type.
    """
    if isinstance(request_data, dict):
        raw_dict = request_data
        raw_ts = raw_dict.get("input_timestamp", raw_dict.get("timestamp"))
        feature_dict: Dict[str, Any] = {
            col: raw_dict[col] for col in CITY_FEATURE_COLUMNS if col in raw_dict
        }
    else:
        # Pydantic model
        feature_dict = {
            col: getattr(request_data, col) for col in CITY_FEATURE_COLUMNS
        }
        raw_ts = getattr(request_data, "input_timestamp", None)

    # Pass input_timestamp through
    if hasattr(raw_ts, "isoformat"):
        feature_dict["input_timestamp"] = raw_ts.isoformat()
    elif raw_ts is not None:
        feature_dict["input_timestamp"] = str(raw_ts)

    # Call ML inference layer without duplicating logic
    return predict_next_hour(feature_dict)
