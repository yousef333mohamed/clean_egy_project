"""Central registry strategy coverage and safety constraints."""

from app.decision.enums import DecisionType


def test_all_supported_strategies_are_registered(decision_registry):
    expected = {
        DecisionType.BIN_ATTENTION_PRIORITY,
        DecisionType.MISSED_COLLECTION_RESPONSE,
        DecisionType.SENSOR_MAINTENANCE_RESPONSE,
        DecisionType.TRUCK_PERFORMANCE_RESPONSE,
        DecisionType.WORKFORCE_OPERATIONAL_RESPONSE,
        DecisionType.REGIONAL_OPERATIONAL_RESPONSE,
        DecisionType.GENERAL_OPERATIONAL_PRIORITY,
    }
    assert {item["decision_type"] for item in decision_registry.catalog()} == expected


def test_every_strategy_has_multiple_actions_and_no_execution_language(decision_registry):
    for item in decision_registry.catalog():
        definition = decision_registry.get(item["decision_type"])
        assert len(definition.action_templates) >= 2
        text = " ".join(template.action for template in definition.action_templates).casefold()
        assert "automatically dispatch" not in text


def test_every_registered_tool_exists(decision_registry, analytics_registry):
    for item in decision_registry.catalog():
        definition = decision_registry.get(item["decision_type"])
        for tool in (*definition.required_analytics_tools, *definition.optional_analytics_tools):
            assert analytics_registry.get(tool).name == tool
