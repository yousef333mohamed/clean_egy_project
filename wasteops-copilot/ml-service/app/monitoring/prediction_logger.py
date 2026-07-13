"""Safe prediction-event logging without complete feature vectors."""

import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def feature_hash(selected_values: dict[str, object]) -> str:
    payload = json.dumps(selected_values, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def log_prediction(
    *, request_id: str, model_name: str, model_version: str, entity_count: int, horizon: int | None, duration_seconds: float, warning_count: int
) -> None:
    logger.info(
        "prediction request_id=%s model=%s version=%s entities=%d horizon=%s duration=%.4f warnings=%d",
        request_id,
        model_name,
        model_version,
        entity_count,
        horizon,
        duration_seconds,
        warning_count,
    )
