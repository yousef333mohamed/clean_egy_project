"""Deterministic time parsing and Cairo boundaries."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.analytics.date_range_parser import DateRangeError, DateRangeParser


@pytest.fixture
def parser(analytics_settings):
    return DateRangeParser(analytics_settings, now=datetime(2026, 7, 13, 10, tzinfo=ZoneInfo("Africa/Cairo")))


@pytest.mark.parametrize(
    ("phrase", "start", "end"),
    [
        ("today", "2026-07-13", "2026-07-13"),
        ("yesterday", "2026-07-12", "2026-07-12"),
        ("this month", "2026-07-01", "2026-07-13"),
        ("last month", "2026-06-01", "2026-06-30"),
        ("last 30 days", "2026-06-14", "2026-07-13"),
        ("March 2026", "2026-03-01", "2026-03-31"),
        ("March", "2026-03-01", "2026-03-31"),
        ("from 2026-01-01 to 2026-01-31", "2026-01-01", "2026-01-31"),
    ],
)
def test_supported_ranges(parser, phrase, start, end):
    result = parser.parse(phrase)
    assert result.start_date.isoformat() == start
    assert result.end_date.isoformat() == end
    assert result.original_phrase == phrase


def test_latest_available_is_explicit(parser):
    result = parser.parse("latest available data")
    assert result.latest_available is True and result.start_date is None


def test_timestamps_use_cairo(parser):
    start, end = parser.parse("today").timestamps()
    assert str(start.tzinfo) == "Africa/Cairo"
    assert end.hour == 23


@pytest.mark.parametrize("phrase", ["from 2026-02-30 to 2026-03-01", "from 2026-03-02 to 2026-03-01", "last 0 days"])
def test_impossible_ranges_rejected(parser, phrase):
    with pytest.raises(DateRangeError):
        parser.parse(phrase)


def test_excessive_range_rejected(parser):
    with pytest.raises(DateRangeError):
        parser.parse("from 2025-01-01 to 2026-07-01")
