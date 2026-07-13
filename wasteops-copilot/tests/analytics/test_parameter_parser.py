"""Allow-list parameter validation."""

import pytest

from app.analytics.parameter_parser import AnalyticsParameterError, ParameterParser
from app.analytics.tool_registry import build_tool_registry


def parser(settings):
    return ParameterParser(build_tool_registry(settings), settings)


def test_arabic_region_and_exact_id_preserved(analytics_settings):
    result = parser(analytics_settings).parse("get_bin_status_summary", {"region": "القاهرة", "bin_id": "BIN-001"})
    assert result.region == "القاهرة" and result.bin_id == "BIN-001"


def test_registered_metric_and_grouping_allowed(analytics_settings):
    result = parser(analytics_settings).parse("rank_workforce_groups", {"metric": "attendance_rate_pct", "group_by": "shift"})
    assert result.group_by == "shift"


@pytest.mark.parametrize("params", [{"metric": "password"}, {"metric": "missed_collection_count; DROP TABLE x"}, {"limit": 201}])
def test_invalid_or_excessive_parameters_rejected(analytics_settings, params):
    with pytest.raises((AnalyticsParameterError, ValueError)):
        parser(analytics_settings).parse("rank_regions_by_operations_metric", params)


def test_unsupported_grouping_rejected(analytics_settings):
    with pytest.raises(AnalyticsParameterError):
        parser(analytics_settings).parse("rank_workforce_groups", {"metric": "attendance_rate_pct", "group_by": "database_column"})


def test_arbitrary_parameter_rejected(analytics_settings):
    with pytest.raises(AnalyticsParameterError):
        parser(analytics_settings).parse("get_operations_summary", {"sql": "SELECT 1"})
