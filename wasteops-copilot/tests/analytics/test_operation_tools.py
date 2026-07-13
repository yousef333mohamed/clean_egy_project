"""Operations tool SQL construction."""

import pytest

from app.analytics.tools.operation_tools import OperationsSummaryTool, RegionalOperationsRankingTool
from app.schemas.analytics_tools import AnalyticsToolParameters


@pytest.mark.parametrize(
    "tool,params",
    [
        (OperationsSummaryTool, {"region": "Greater Cairo"}),
        (RegionalOperationsRankingTool, {"metric": "missed_collection_count", "limit": 5}),
    ],
)
async def test_operations_tools_build_bounded_parameterized_queries(tool, params, analytics_settings, recording_executor):
    instance = tool(analytics_settings)
    instance.executor = recording_executor
    result = await instance.execute(AnalyticsToolParameters(**params), object())
    assert result.tool_name == instance.name
    assert "%(" in recording_executor.statements[0][2]
    assert "Greater Cairo" not in recording_executor.statements[0][2]
