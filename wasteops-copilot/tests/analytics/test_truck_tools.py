"""Truck metric and deterministic anomaly SQL."""

import pytest

from app.analytics.tools.truck_tools import TruckAnomalyTool, TruckPerformanceSummaryTool, TruckRankingTool
from app.schemas.analytics_tools import AnalyticsToolParameters


@pytest.mark.parametrize(
    "tool,params",
    [
        (TruckPerformanceSummaryTool, {}),
        (TruckRankingTool, {"metric": "truck_utilization_pct"}),
        (TruckAnomalyTool, {"truck_id": "TRUCK-1"}),
    ],
)
async def test_truck_tools_compile(tool, params, analytics_settings, recording_executor):
    instance = tool(analytics_settings)
    instance.executor = recording_executor
    result = await instance.execute(AnalyticsToolParameters(**params), object())
    assert result.tool_name == instance.name
    assert "TRUCK-1" not in recording_executor.statements[0][2]


async def test_anomaly_rules_are_explained_and_not_predictions(analytics_settings, recording_executor):
    tool = TruckAnomalyTool(analytics_settings)
    tool.executor = recording_executor
    result = await tool.execute(AnalyticsToolParameters(), object())
    sql = recording_executor.statements[0][2]
    assert "historical_average_fuel_l" in sql
    assert any("not AI predictions" in note for note in result.notes)
