"""Small non-causal explanation factor formatter."""

from app.schemas.common import ExplanationFactor


SAFE_FEATURES = frozenset(
    {
        "current_fill_level_pct",
        "fill_change_6h",
        "average_fill_rate_24h",
        "hours_since_last_collection",
        "overflow_probability",
        "current_urgency",
        "service_history",
        "operational_context",
        "sensor_reliability",
        "trip_behavior_deviation",
        "historical_missed_rate_28d",
        "recent_required_workers_28d",
    }
)


def safe_factors(raw: list[dict], limit: int = 5) -> list[ExplanationFactor]:
    filtered = [item for item in raw if item.get("feature") in SAFE_FEATURES]
    filtered.sort(key=lambda item: abs(float(item.get("contribution", 0))), reverse=True)
    return [ExplanationFactor.model_validate(item) for item in filtered[:limit]]
