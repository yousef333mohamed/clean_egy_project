"""Workforce summary and grouping SQL."""

import pytest

from app.analytics.tools.workforce_tools import WorkforceRankingTool, WorkforceSummaryTool
from app.schemas.analytics_tools import AnalyticsToolParameters


@pytest.mark.parametrize("tool,params", [(WorkforceSummaryTool, {}), (WorkforceRankingTool, {"metric": "average_performance_score", "group_by": "shift"})])
async def test_workforce_tools_compile_with_score_denominators(tool, params, analytics_settings, recording_executor):
    instance = tool(analytics_settings)
    instance.executor = recording_executor
    result = await instance.execute(AnalyticsToolParameters(**params), object())
    assert result.tool_name == instance.name
    assert "performance" in recording_executor.statements[0][2].casefold()
