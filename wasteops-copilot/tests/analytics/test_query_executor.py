"""Row limits and JSON-safe controlled execution."""

from decimal import Decimal

from sqlalchemy import literal, select

from app.analytics.query_executor import QueryExecutor
from tests.analytics.conftest import FakeSession


async def test_executor_applies_limit_and_preserves_null(analytics_settings):
    session = FakeSession([{"value": Decimal("12.50"), "missing": None}])
    rows = await QueryExecutor(analytics_settings).execute(session, select(literal(1).label("value")), tool_name="safe_tool", limit=999)
    assert rows == [{"value": 12.5, "missing": None}]
    assert session.statements[0]._limit_clause.value == analytics_settings.analytics_max_limit
