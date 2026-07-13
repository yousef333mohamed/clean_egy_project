"""Versioned feature definitions, including availability and leakage controls."""

from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class FeatureDefinition:
    feature_name: str
    domain: str
    data_type: Literal["float", "integer", "boolean", "category"]
    source: str
    description: str
    lookback_window: str
    aggregation: str
    nullable: bool
    default_strategy: str
    validation_rules: dict[str, Any]
    availability_delay: str
    used_by_models: tuple[str, ...]
    leakage_risk: str


def _bin(name: str, source: str, description: str, *, window: str = "current", aggregation: str = "latest", nullable: bool = True) -> FeatureDefinition:
    return FeatureDefinition(
        name,
        "bin",
        "float",
        source,
        description,
        window,
        aggregation,
        nullable,
        "median_plus_missing_indicator",
        {"min": 0},
        "up to 15 minutes",
        ("bin-overflow", "collection-priority"),
        "Exclude records after prediction timestamp",
    )


FEATURES: tuple[FeatureDefinition, ...] = (
    _bin("current_fill_level_pct", "smart_bin_readings.fill_level_pct", "Latest known fill percentage", nullable=False),
    _bin("fill_change_3h", "smart_bin_readings.fill_level_pct", "Point-in-time fill change", window="3h", aggregation="latest-minus-earliest"),
    _bin("fill_change_6h", "smart_bin_readings.fill_level_pct", "Point-in-time fill change", window="6h", aggregation="latest-minus-earliest"),
    _bin("fill_change_12h", "smart_bin_readings.fill_level_pct", "Point-in-time fill change", window="12h", aggregation="latest-minus-earliest"),
    _bin("fill_change_24h", "smart_bin_readings.fill_level_pct", "Point-in-time fill change", window="24h", aggregation="latest-minus-earliest"),
    _bin("average_fill_rate_24h", "smart_bin_readings.fill_level_pct", "Average hourly fill rate", window="24h", aggregation="slope"),
    _bin("maximum_fill_24h", "smart_bin_readings.fill_level_pct", "Maximum prior fill", window="24h", aggregation="max"),
    _bin("hours_since_last_collection", "smart_bin_readings.last_collected_at", "Elapsed hours known at prediction time"),
    FeatureDefinition(
        "sensor_fault_flag",
        "bin",
        "boolean",
        "smart_bin_readings.sensor_status",
        "Known sensor fault",
        "current",
        "latest",
        False,
        "false_only_when_observed_healthy",
        {},
        "up to 15 minutes",
        ("bin-overflow", "collection-priority"),
        "Do not infer later repair state",
    ),
    FeatureDefinition(
        "region",
        "bin",
        "category",
        "smart_bins.region",
        "Operational region",
        "static",
        "latest_effective",
        False,
        "unknown_category",
        {},
        "effective-dated",
        ("bin-overflow", "collection-priority"),
        "Use effective value as of prediction time",
    ),
    FeatureDefinition(
        "fuel_efficiency_km_per_l",
        "truck",
        "float",
        "truck_trip_logs.distance_km,fuel_consumed_l",
        "Observed trip efficiency",
        "trip",
        "ratio",
        True,
        "median_plus_missing_indicator",
        {"min": 0},
        "after trip close",
        ("truck-anomaly",),
        "Only score closed trips",
    ),
    FeatureDefinition(
        "historical_missed_rate_28d",
        "operations",
        "float",
        "operational_daily.missed_collections",
        "Prior regional miss rate",
        "28d",
        "mean",
        True,
        "regional_prior_plus_missing_indicator",
        {"min": 0, "max": 1},
        "next-day",
        ("missed-collection",),
        "Outcome day excluded",
    ),
    FeatureDefinition(
        "recent_required_workers_28d",
        "workforce",
        "float",
        "workforce_attendance",
        "Recent observed staffing requirement",
        "28d",
        "mean",
        True,
        "regional_shift_prior",
        {"min": 0},
        "next-day",
        ("workforce-forecast",),
        "Forecast date excluded",
    ),
)

FEATURE_VERSION = "1.0.0"


def definitions_for(model_name: str) -> list[FeatureDefinition]:
    return [feature for feature in FEATURES if model_name in feature.used_by_models]


def export_registry() -> list[dict[str, Any]]:
    return [asdict(feature) for feature in FEATURES]
