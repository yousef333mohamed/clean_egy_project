"""Single typed registry for supported decision strategies and actions."""

from dataclasses import dataclass

from app.decision.enums import ActionCategory, DecisionType


@dataclass(frozen=True)
class ActionTemplate:
    category: ActionCategory
    title: str
    action: str
    expected_impact: tuple[str, ...]
    operational_requirements: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.expected_impact, str):
            object.__setattr__(self, "expected_impact", (self.expected_impact,))
        if isinstance(self.operational_requirements, str):
            object.__setattr__(self, "operational_requirements", (self.operational_requirements,))


@dataclass(frozen=True)
class DecisionDefinition:
    decision_type: DecisionType
    description: str
    required_analytics_tools: tuple[str, ...]
    optional_analytics_tools: tuple[str, ...]
    recommended_document_types: tuple[str, ...]
    document_queries: tuple[str, ...]
    required_evidence_categories: tuple[str, ...]
    action_templates: tuple[ActionTemplate, ...]
    scoring_criteria: tuple[str, ...]
    unsupported_conditions: tuple[str, ...]
    example_questions: tuple[str, ...]


class DecisionRegistry:
    def __init__(self, definitions: list[DecisionDefinition]) -> None:
        self._definitions = {item.decision_type: item for item in definitions}

    def get(self, decision_type: DecisionType) -> DecisionDefinition:
        try:
            return self._definitions[decision_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported decision type: {decision_type}") from exc

    def catalog(self) -> list[dict[str, object]]:
        return [
            {
                "decision_type": item.decision_type,
                "description": item.description,
                "example_questions": item.example_questions,
                "requires_human_approval": True,
            }
            for item in self._definitions.values()
        ]


def build_decision_registry() -> DecisionRegistry:
    from app.decision.strategies.bin_attention import definition as bin_attention
    from app.decision.strategies.missed_collection import definition as missed_collection
    from app.decision.strategies.operational_overview import definitions as overview_definitions
    from app.decision.strategies.sensor_maintenance import definition as sensor_maintenance
    from app.decision.strategies.truck_performance import definition as truck_performance
    from app.decision.strategies.workforce_response import definition as workforce_response

    return DecisionRegistry([bin_attention(), missed_collection(), sensor_maintenance(), truck_performance(), workforce_response(), *overview_definitions()])
