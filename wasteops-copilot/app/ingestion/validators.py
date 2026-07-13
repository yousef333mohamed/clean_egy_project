"""Registry-driven conversion and dataset-specific row validation."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.ingestion.converters import ConversionError, to_boolean, to_date, to_decimal, to_integer, to_string, to_utc_timestamp
from app.ingestion.registry import DatasetDefinition


@dataclass(frozen=True, slots=True)
class RowValidationError:
    """Safe, reportable reason for rejecting one source row."""

    code: str
    message: str


class RecordValidationError(ValueError):
    """Raised when a converted record violates a business rule."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def convert_record(raw: dict[str, Any], definition: DatasetDefinition, source_timezone: str) -> dict[str, Any]:
    """Convert one raw record using only the central registry definition."""
    converted: dict[str, Any] = {}
    for column in definition.required_columns:
        value = raw.get(column)
        nullable = column in definition.nullable_columns
        try:
            if column in definition.boolean_columns:
                converted[column] = to_boolean(value, nullable=nullable)
            elif column in definition.date_columns:
                converted[column] = to_date(value, nullable=nullable)
            elif column in definition.timestamp_columns:
                converted[column] = to_utc_timestamp(value, source_timezone, nullable=nullable)
            elif column in definition.integer_columns:
                converted[column] = to_integer(value, nullable=nullable)
            elif column in definition.decimal_columns:
                converted[column] = to_decimal(value, nullable=nullable)
            else:
                converted[column] = to_string(value, nullable=nullable)
        except ConversionError as exc:
            raise RecordValidationError("CONVERSION_ERROR", f"{column}: {exc}") from exc
    validate_record(converted, definition.name)
    return converted


def _between(record: dict[str, Any], column: str, minimum: Decimal | int, maximum: Decimal | int) -> None:
    value = record[column]
    if value is not None and not minimum <= value <= maximum:
        raise RecordValidationError("OUT_OF_RANGE", f"{column} must be between {minimum} and {maximum}")


def _nonnegative(record: dict[str, Any], *columns: str) -> None:
    for column in columns:
        value = record[column]
        if value is not None and value < 0:
            raise RecordValidationError("OUT_OF_RANGE", f"{column} must be non-negative")


def _positive(record: dict[str, Any], column: str) -> None:
    if record[column] <= 0:
        raise RecordValidationError("OUT_OF_RANGE", f"{column} must be greater than zero")


def validate_record(record: dict[str, Any], dataset: str) -> None:
    """Apply row-level domain constraints after successful conversion."""
    if dataset == "smart_bins":
        _between(record, "latitude", -90, 90)
        _between(record, "longitude", -180, 180)
        _positive(record, "capacity_liters")
    elif dataset == "smart_bin_readings":
        _between(record, "fill_level_pct", 0, 100)
        _nonnegative(record, "waste_weight_kg")
        _between(record, "humidity_pct", 0, 100)
        _between(record, "battery_level_pct", 0, 100)
    elif dataset == "operational_daily":
        _nonnegative(record, "service_completion_time_min")
    elif dataset == "environmental_daily":
        _nonnegative(record, "rainfall_mm")
    elif dataset == "trucks":
        _positive(record, "capacity_kg")
        if not 1980 <= record["model_year"] <= 2100:
            raise RecordValidationError("OUT_OF_RANGE", "model_year must be between 1980 and 2100")
    elif dataset == "truck_trip_logs":
        _nonnegative(record, "distance_km", "fuel_consumed_l", "load_kg", "avg_speed_kmh", "stops_completed", "trip_duration_min")
    elif dataset == "workforce":
        _nonnegative(record, "experience_years")
    elif dataset == "workforce_attendance":
        _nonnegative(record, "completed_tasks", "overtime_hours")
        _between(record, "performance_score", 0, 100)
