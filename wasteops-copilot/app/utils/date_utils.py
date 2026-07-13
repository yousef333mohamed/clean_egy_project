"""Date parsing helpers."""

from datetime import date, datetime


def parse_date(value: object) -> date | None:
    """Parse a date-like value, returning None for missing values."""
    if value is None or str(value).strip() == "":
        return None
    return datetime.fromisoformat(str(value)).date()


def parse_datetime(value: object) -> datetime | None:
    """Parse an ISO timestamp, returning None for missing values."""
    if value is None or str(value).strip() == "":
        return None
    return datetime.fromisoformat(str(value))
