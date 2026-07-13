"""Registry revalidation before tool execution."""

import pytest

from app.analytics.analytics_service import AnalyticsService
from app.analytics.tool_registry import UnknownAnalyticsTool, build_tool_registry


async def test_unknown_tool_never_executes(analytics_settings):
    service = AnalyticsService(build_tool_registry(analytics_settings), analytics_settings)
    with pytest.raises(UnknownAnalyticsTool):
        await service.execute("DROP TABLE", {}, object())
