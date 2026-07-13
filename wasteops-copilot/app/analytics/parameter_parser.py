"""Tool-specific allow-list validation and limit enforcement."""

from typing import Any

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.analytics_tools import AnalyticsToolParameters


class AnalyticsParameterError(ValueError):
    """Tool parameters fail the published contract."""


class ParameterParser:
    def __init__(self, registry, settings: Settings | None = None) -> None:
        self.registry = registry
        self.settings = settings or get_settings()

    def parse(self, tool_name: str, raw: dict[str, Any] | AnalyticsToolParameters) -> AnalyticsToolParameters:
        tool = self.registry.get(tool_name)
        try:
            params = raw if isinstance(raw, AnalyticsToolParameters) else AnalyticsToolParameters.model_validate(raw)
        except ValidationError as exc:
            raise AnalyticsParameterError(str(exc)) from exc
        values = params.model_dump(exclude_none=True, exclude_defaults=True)
        supplied = set(values) - {"latest_available"}
        unsupported = supplied - set(tool.allowed_parameters)
        if unsupported:
            raise AnalyticsParameterError(f"Unsupported parameters for {tool_name}: {', '.join(sorted(unsupported))}")
        missing = [name for name in tool.required_parameters if getattr(params, name) is None]
        if missing:
            raise AnalyticsParameterError(f"Missing required parameters for {tool_name}: {', '.join(missing)}")
        if params.metric and params.metric not in tool.supported_metrics:
            raise AnalyticsParameterError(f"Unsupported metric for {tool_name}: {params.metric}")
        if params.group_by and params.group_by not in tool.allowed_groupings:
            raise AnalyticsParameterError(f"Unsupported grouping for {tool_name}: {params.group_by}")
        limit = params.limit or min(tool.maximum_result_size, self.settings.analytics_default_limit)
        if limit > min(tool.maximum_result_size, self.settings.analytics_max_limit):
            raise AnalyticsParameterError("limit exceeds the permitted maximum")
        if params.start_date and params.end_date and (params.end_date - params.start_date).days + 1 > self.settings.analytics_max_date_range_days:
            raise AnalyticsParameterError("date range exceeds the configured maximum")
        return params.model_copy(update={"limit": limit})
