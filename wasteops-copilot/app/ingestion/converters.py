"""Strict, missing-value-aware CSV value converters."""

import math
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


class ConversionError(ValueError):
    """A value cannot be converted without guessing."""


def is_missing(value: Any) -> bool:
    """Recognize pandas and CSV missing values without coercing valid values."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().lower() in {"nan", "nat", "null", "none"}
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def to_string(value: Any, *, nullable: bool = False) -> str | None:
    """Trim text while retaining casing and Arabic characters."""
    if is_missing(value):
        if nullable:
            return None
        raise ConversionError("value is required")
    result = str(value).strip()
    if not result and not nullable:
        raise ConversionError("value is required")
    return result or None


def to_date(value: Any, *, nullable: bool = False) -> date | None:
    """Parse an ISO date without timezone conversion."""
    if is_missing(value):
        if nullable:
            return None
        raise ConversionError("date is required")
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ConversionError(f"invalid ISO date: {value!r}") from exc


def to_utc_timestamp(value: Any, source_timezone: str, *, nullable: bool = False) -> datetime | None:
    """Interpret a naive source timestamp in its local zone and return UTC."""
    if is_missing(value):
        if nullable:
            return None
        raise ConversionError("timestamp is required")
    try:
        parsed = datetime.fromisoformat(str(value).strip())
        zone = ZoneInfo(source_timezone)
    except (TypeError, ValueError, KeyError) as exc:
        raise ConversionError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(UTC)


def to_boolean(value: Any, *, nullable: bool = False) -> bool | None:
    """Convert an explicit boolean token and reject ambiguous values."""
    if is_missing(value):
        if nullable:
            return None
        raise ConversionError("boolean is required")
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    token = str(value).strip().lower()
    if token in {"true", "1", "yes"}:
        return True
    if token in {"false", "0", "no"}:
        return False
    raise ConversionError(f"ambiguous boolean: {value!r}")


def to_decimal(value: Any, *, nullable: bool = False) -> Decimal | None:
    """Convert a finite decimal, preserving missing values as None."""
    if is_missing(value):
        if nullable:
            return None
        raise ConversionError("number is required")
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ConversionError(f"invalid number: {value!r}") from exc
    if not result.is_finite():
        raise ConversionError(f"number must be finite: {value!r}")
    return result


def to_integer(value: Any, *, nullable: bool = False) -> int | None:
    """Convert an exact integer and reject fractional values."""
    number = to_decimal(value, nullable=nullable)
    if number is None:
        return None
    if number != number.to_integral_value() or math.isinf(float(number)):
        raise ConversionError(f"invalid integer: {value!r}")
    return int(number)
