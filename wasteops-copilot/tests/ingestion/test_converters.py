"""Unit tests for strict missing-aware typed conversion."""

from datetime import UTC, date, datetime

import pandas as pd
import pytest

from app.ingestion.converters import ConversionError, to_boolean, to_date, to_decimal, to_string, to_utc_timestamp


def test_arabic_text_is_trimmed_but_preserved() -> None:
    assert to_string("  القاهرة  ") == "القاهرة"


def test_date_and_cairo_timestamp_conversion() -> None:
    assert to_date("2026-01-01") == date(2026, 1, 1)
    assert to_utc_timestamp("2026-01-01T00:00:00", "Africa/Cairo") == datetime(2025, 12, 31, 22, tzinfo=UTC)


@pytest.mark.parametrize(("value", "expected"), [("true", True), ("False", False), (1, True), (0, False), ("yes", True), ("no", False)])
def test_safe_boolean_tokens(value: object, expected: bool) -> None:
    assert to_boolean(value) is expected


def test_ambiguous_boolean_is_rejected() -> None:
    with pytest.raises(ConversionError):
        to_boolean("sometimes")


@pytest.mark.parametrize("value", [None, "", float("nan"), pd.NA, pd.NaT])
def test_missing_numeric_is_none_when_nullable(value: object) -> None:
    assert to_decimal(value, nullable=True) is None


def test_infinity_is_rejected() -> None:
    with pytest.raises(ConversionError):
        to_decimal("Infinity")
