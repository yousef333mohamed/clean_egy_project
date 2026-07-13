"""Cross-domain overview effective-date labels."""

from app.analytics.tools.overview_tools import OperationalOverviewTool
from app.schemas.analytics_tools import AnalyticsToolParameters


async def test_overview_compiles_and_labels_effective_dates(analytics_settings, recording_executor):
    tool = OperationalOverviewTool(analytics_settings)
    tool.executor = recording_executor
    result = await tool.execute(AnalyticsToolParameters(region="Delta"), object())
    sql = recording_executor.statements[0][2]
    assert "operations_effective_date" in sql and "trucks_effective_date" in sql
    assert any("coverage may differ" in note for note in result.notes)
