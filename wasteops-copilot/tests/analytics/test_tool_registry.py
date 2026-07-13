"""Static catalog security and completeness."""

import pytest

from app.analytics.tool_registry import UnknownAnalyticsTool, build_tool_registry


def test_all_required_tools_registered_without_sql(analytics_settings):
    registry = build_tool_registry(analytics_settings)
    assert len(registry.list()) == 13
    assert {item["name"] for item in registry.catalog()} >= {"get_operations_summary", "get_operational_overview", "detect_truck_rule_anomalies"}
    assert "sql" not in str(registry.catalog()).casefold()


def test_unknown_tool_rejected(analytics_settings):
    with pytest.raises(UnknownAnalyticsTool):
        build_tool_registry(analytics_settings).get("run_user_sql")
