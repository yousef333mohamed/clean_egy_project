"""General and regional operational-priority definitions."""

from app.decision.decision_registry import ActionTemplate, DecisionDefinition
from app.decision.enums import ActionCategory, DecisionType


def _actions() -> tuple[ActionTemplate, ...]:
    return (
        ActionTemplate(
            ActionCategory.COMBINED_OPERATIONAL_REVIEW,
            "Review highest supported priorities",
            "Review the strongest current database conditions together before authorizing any response.",
            "Focus management attention on evidence-supported service conditions.",
            "Manager review and confirmed resources",
        ),
        ActionTemplate(
            ActionCategory.PRIORITIZE_COLLECTION_REVIEW,
            "Review collection continuity",
            "Review critical bins and missed-collection evidence for service-continuity implications.",
            "Protect collection-service continuity.",
            "Confirmed collection capacity",
        ),
        ActionTemplate(
            ActionCategory.REQUEST_INSPECTION,
            "Review maintenance priorities",
            "Request inspection review for current sensor or truck rule anomalies.",
            "Reduce unresolved equipment and telemetry risk.",
            "Maintenance capacity confirmation",
        ),
        ActionTemplate(
            ActionCategory.REVIEW_ATTENDANCE_COVERAGE,
            "Review workforce coverage",
            "Review attendance evidence before considering any resource assignment.",
            "Identify supported coverage concerns.",
            "Current shift requirements",
        ),
        ActionTemplate(
            ActionCategory.CONTINUE_MONITORING,
            "Continue monitored operations",
            "Continue monitoring when no high-priority current condition is supported.",
            "Maintain oversight without unsupported intervention.",
            "Reliable current data feeds",
        ),
    )


def definitions() -> tuple[DecisionDefinition, DecisionDefinition]:
    common = dict(
        optional_analytics_tools=(),
        recommended_document_types=("operational_sop", "incident_procedure"),
        document_queries=("operational priority escalation and review procedure",),
        required_evidence_categories=("operational_overview", "configured_rules"),
        action_templates=_actions(),
        scoring_criteria=("affected operations", "current urgency", "continuity risk", "known feasibility", "procedure authority"),
        unsupported_conditions=("route optimization", "automatic dispatch", "future prediction"),
    )
    general = DecisionDefinition(
        decision_type=DecisionType.GENERAL_OPERATIONAL_PRIORITY,
        description="Rank current operational priorities across supported domains.",
        required_analytics_tools=(
            "get_operational_overview",
            "rank_regions_by_operations_metric",
            "list_critical_bins",
            "list_low_battery_bins",
            "list_sensor_fault_bins",
            "detect_truck_rule_anomalies",
            "get_workforce_summary",
        ),
        example_questions=("What should we prioritize based on the latest available data?",),
        **common,
    )
    regional = DecisionDefinition(
        decision_type=DecisionType.REGIONAL_OPERATIONAL_RESPONSE,
        description="Review supported operational priorities for one region.",
        required_analytics_tools=("get_operational_overview", "rank_regions_by_operations_metric"),
        example_questions=("What is the best operational response for Greater Cairo?",),
        **common,
    )
    return general, regional
