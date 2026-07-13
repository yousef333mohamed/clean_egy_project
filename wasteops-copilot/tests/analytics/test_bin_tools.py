"""Bin summary and latest-reading query construction."""

import pytest

from app.analytics.tools.bin_tools import BinStatusSummaryTool, CriticalBinsTool, LowBatteryBinsTool, SensorFaultBinsTool
from app.schemas.analytics_tools import AnalyticsToolParameters


@pytest.mark.parametrize("tool", [BinStatusSummaryTool, CriticalBinsTool, LowBatteryBinsTool, SensorFaultBinsTool])
async def test_bin_tools_compile_latest_and_threshold_rules(tool, analytics_settings, recording_executor):
    instance = tool(analytics_settings)
    instance.executor = recording_executor
    result = await instance.execute(AnalyticsToolParameters(region="القاهرة", limit=10), object())
    sql = recording_executor.statements[0][2]
    assert result.tool_name == instance.name
    assert "القاهرة" not in sql
    if tool is not BinStatusSummaryTool:
        assert "row_number" in sql.casefold()


async def test_threshold_notes_are_not_official_policy(analytics_settings, recording_executor):
    tool = CriticalBinsTool(analytics_settings)
    tool.executor = recording_executor
    result = await tool.execute(AnalyticsToolParameters(), object())
    assert any("not marked as an official policy" in note for note in result.notes)
