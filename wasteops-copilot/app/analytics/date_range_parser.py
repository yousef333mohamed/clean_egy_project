"""Deterministic English/Arabic date-range parsing in application time."""

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import Settings, get_settings

MONTHS = {name.casefold(): number for number, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.casefold(): number for number, name in enumerate(calendar.month_abbr) if name})
ARABIC_MONTHS = {
    "يناير": 1,
    "فبراير": 2,
    "مارس": 3,
    "أبريل": 4,
    "ابريل": 4,
    "مايو": 5,
    "يونيو": 6,
    "يوليو": 7,
    "أغسطس": 8,
    "اغسطس": 8,
    "سبتمبر": 9,
    "أكتوبر": 10,
    "اكتوبر": 10,
    "نوفمبر": 11,
    "ديسمبر": 12,
}


class DateRangeError(ValueError):
    """The requested phrase is invalid, ambiguous, or exceeds policy."""


@dataclass(frozen=True)
class ParsedDateRange:
    start_date: date | None
    end_date: date | None
    original_phrase: str
    latest_available: bool = False

    def timestamps(self, timezone: str = "Africa/Cairo") -> tuple[datetime | None, datetime | None]:
        if not self.start_date or not self.end_date:
            return None, None
        tz = ZoneInfo(timezone)
        return datetime.combine(self.start_date, datetime.min.time(), tz), datetime.combine(self.end_date, datetime.max.time(), tz)


class DateRangeParser:
    """Resolve explicit supported phrases without consulting dataset recency."""

    def __init__(self, settings: Settings | None = None, *, now: datetime | None = None) -> None:
        self.settings = settings or get_settings()
        self.timezone = ZoneInfo(self.settings.source_timezone)
        self.now = now.astimezone(self.timezone) if now else datetime.now(self.timezone)

    def parse(self, phrase: str) -> ParsedDateRange:
        original = phrase.strip()
        value = " ".join(original.casefold().split())
        today = self.now.date()
        if value in {"latest available data", "latest data", "أحدث بيانات متاحة", "احدث بيانات متاحة"}:
            return ParsedDateRange(None, None, original, True)
        relative = {
            "today": (today, today),
            "اليوم": (today, today),
            "yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
            "أمس": (today - timedelta(days=1), today - timedelta(days=1)),
        }
        if value in relative:
            start, end = relative[value]
            return self._validated(start, end, original)
        if value in {"this week", "هذا الأسبوع", "هذا الاسبوع"}:
            start = today - timedelta(days=today.weekday())
            return self._validated(start, today, original)
        if value in {"last week", "الأسبوع الماضي", "الاسبوع الماضي"}:
            end = today - timedelta(days=today.weekday() + 1)
            return self._validated(end - timedelta(days=6), end, original)
        if value in {"this month", "هذا الشهر"}:
            return self._validated(today.replace(day=1), today, original)
        if value in {"last month", "الشهر الماضي"}:
            end = today.replace(day=1) - timedelta(days=1)
            return self._validated(end.replace(day=1), end, original)
        days = re.fullmatch(r"last\s+(\d{1,3})\s+days", value) or re.fullmatch(r"(?:آخر|اخر)\s+(\d{1,3})\s+(?:يوم|يوما|أيام)", value)
        if days:
            count = int(days.group(1))
            if count < 1:
                raise DateRangeError("day count must be positive")
            return self._validated(today - timedelta(days=count - 1), today, original)
        explicit = re.fullmatch(r"from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})", value)
        if explicit:
            try:
                return self._validated(date.fromisoformat(explicit.group(1)), date.fromisoformat(explicit.group(2)), original)
            except ValueError as exc:
                raise DateRangeError("invalid calendar date") from exc
        month_year = re.fullmatch(r"([\w\u0600-\u06ff]+)\s+(\d{4})", value)
        if month_year:
            month = MONTHS.get(month_year.group(1)) or ARABIC_MONTHS.get(month_year.group(1))
            if month:
                year = int(month_year.group(2))
                end_day = calendar.monthrange(year, month)[1]
                return self._validated(date(year, month, 1), date(year, month, end_day), original)
        month = MONTHS.get(value) or ARABIC_MONTHS.get(value)
        if month:
            year = self.now.year
            return self._validated(date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]), original)
        raise DateRangeError("unsupported or ambiguous date range")

    def _validated(self, start: date, end: date, original: str) -> ParsedDateRange:
        if start > end:
            raise DateRangeError("start date must not be after end date")
        if (end - start).days + 1 > self.settings.analytics_max_date_range_days:
            raise DateRangeError("date range exceeds the configured maximum")
        return ParsedDateRange(start, end, original)
