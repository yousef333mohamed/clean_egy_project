"""Request, asset, model, and freshness validation."""

from datetime import datetime


class PredictionValidationError(ValueError):
    pass


def validate_batch(entity_ids: list[str], maximum: int) -> list[str]:
    cleaned = list(dict.fromkeys(item.strip() for item in entity_ids if item.strip()))
    if not cleaned:
        raise PredictionValidationError("At least one entity ID is required")
    if len(cleaned) > maximum:
        raise PredictionValidationError(f"Batch exceeds maximum of {maximum}")
    return cleaned


def freshness(
    feature_timestamp: datetime, prediction_timestamp: datetime, maximum_age_seconds: int, *, degraded_allowed: bool = False
) -> tuple[int, list[str]]:
    age = max(0, int((prediction_timestamp - feature_timestamp).total_seconds()))
    if feature_timestamp > prediction_timestamp:
        raise PredictionValidationError("Feature timestamp occurs after prediction timestamp")
    if age > maximum_age_seconds:
        warning = f"Feature data is stale ({age} seconds old; maximum {maximum_age_seconds})."
        if not degraded_allowed:
            raise PredictionValidationError(warning)
        return age, [warning, "Prediction is degraded and must not be presented as current."]
    return age, []
