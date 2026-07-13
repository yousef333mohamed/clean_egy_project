"""Environmental region-day summary SQL."""

from app.analytics.tools.environment_tools import EnvironmentalSummaryTool
from app.schemas.analytics_tools import AnalyticsToolParameters


async def test_environment_tool_labels_region_day_semantics(analytics_settings, recording_executor):
    tool = EnvironmentalSummaryTool(analytics_settings)
    tool.executor = recording_executor
    result = await tool.execute(AnalyticsToolParameters(traffic_level="High"), object())
    assert any("region-day" in note for note in result.notes)
    assert "High" not in recording_executor.statements[0][2]
