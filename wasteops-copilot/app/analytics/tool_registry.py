"""Analytics tool contract and immutable allow-listed registry."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.enums import AnalyticsDomain
from app.schemas.analytics_tools import AnalyticsToolParameters, AnalyticsToolResult


class AnalyticsTool(Protocol):
    name: str
    description: str
    domain: AnalyticsDomain
    supported_metrics: tuple[str, ...]
    required_parameters: tuple[str, ...]
    allowed_parameters: tuple[str, ...]
    allowed_groupings: tuple[str, ...]
    maximum_result_size: int
    example_questions: tuple[str, ...]

    async def execute(self, params: AnalyticsToolParameters, session: AsyncSession) -> AnalyticsToolResult: ...


class UnknownAnalyticsTool(ValueError):
    """A route attempted to select an unregistered tool."""


class AnalyticsToolRegistry:
    def __init__(self, tools: Sequence[AnalyticsTool]) -> None:
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("analytics tool names must be unique")

    def get(self, name: str) -> AnalyticsTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise UnknownAnalyticsTool(f"Unknown analytics tool: {name}") from exc

    def list(self) -> list[AnalyticsTool]:
        return list(self._tools.values())

    def catalog(self) -> list[dict[str, object]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "domain": tool.domain,
                "supported_metrics": tool.supported_metrics,
                "required_parameters": tool.required_parameters,
                "allowed_parameters": tool.allowed_parameters,
                "allowed_groupings": tool.allowed_groupings,
                "maximum_result_size": tool.maximum_result_size,
                "example_questions": tool.example_questions,
            }
            for tool in self.list()
        ]


def build_tool_registry(settings=None) -> AnalyticsToolRegistry:
    """Construct all approved tools; no dynamic imports or user extensions."""
    from app.analytics.tools.bin_tools import BinStatusSummaryTool, CriticalBinsTool, LowBatteryBinsTool, SensorFaultBinsTool
    from app.analytics.tools.environment_tools import EnvironmentalSummaryTool
    from app.analytics.tools.operation_tools import OperationsSummaryTool, RegionalOperationsRankingTool
    from app.analytics.tools.overview_tools import OperationalOverviewTool
    from app.analytics.tools.truck_tools import TruckAnomalyTool, TruckPerformanceSummaryTool, TruckRankingTool
    from app.analytics.tools.workforce_tools import WorkforceRankingTool, WorkforceSummaryTool

    return AnalyticsToolRegistry(
        [
            OperationsSummaryTool(settings),
            RegionalOperationsRankingTool(settings),
            BinStatusSummaryTool(settings),
            CriticalBinsTool(settings),
            LowBatteryBinsTool(settings),
            SensorFaultBinsTool(settings),
            TruckPerformanceSummaryTool(settings),
            TruckRankingTool(settings),
            TruckAnomalyTool(settings),
            WorkforceSummaryTool(settings),
            WorkforceRankingTool(settings),
            EnvironmentalSummaryTool(settings),
            OperationalOverviewTool(settings),
        ]
    )
