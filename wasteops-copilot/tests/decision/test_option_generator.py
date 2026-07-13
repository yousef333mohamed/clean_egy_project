"""Registered, distinct, non-autonomous action generation."""

from app.decision.enums import DecisionType
from app.decision.option_generator import OptionGenerator
from app.schemas.decision import DecisionConstraints, DecisionRequest


def test_generates_multiple_registered_distinct_options(decision_registry, decision_settings, evidence_factory):
    request = DecisionRequest(question="Which bins need attention?", constraints=DecisionConstraints(maximum_actions=3))
    options = OptionGenerator(decision_registry, decision_settings).generate(request, DecisionType.BIN_ATTENTION_PRIORITY, [evidence_factory()])
    assert 2 <= len(options) <= 3
    assert len({item.action_category for item in options}) == len(options)
    allowed = {item.category for item in decision_registry.get(DecisionType.BIN_ATTENTION_PRIORITY).action_templates}
    assert {item.action_category for item in options} <= allowed


def test_does_not_assign_resources_or_execute(decision_registry, decision_settings, evidence_factory):
    options = OptionGenerator(decision_registry, decision_settings).generate(
        DecisionRequest(question="Act"), DecisionType.TRUCK_PERFORMANCE_RESPONSE, [evidence_factory(category="truck_performance")]
    )
    text = " ".join(item.action for item in options).casefold()
    assert "automatically" not in text and "dispatch" not in text
    assert all(item.assumptions for item in options)


def test_monitoring_ranks_first_when_no_condition(decision_registry, decision_settings, evidence_factory):
    empty = evidence_factory(supporting_values={"has_data": False, "result_row_count": 0})
    options = OptionGenerator(decision_registry, decision_settings).generate(
        DecisionRequest(question="What now?"), DecisionType.BIN_ATTENTION_PRIORITY, [empty]
    )
    assert options[0].action_category == "CONTINUE_MONITORING"
