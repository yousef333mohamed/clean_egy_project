"""Missed-collection response definition."""

from app.decision.decision_registry import ActionTemplate, DecisionDefinition
from app.decision.enums import ActionCategory, DecisionType


def definition() -> DecisionDefinition:
    return DecisionDefinition(
        DecisionType.MISSED_COLLECTION_RESPONSE,
        "Recommend review and escalation options for historical missed-collection evidence.",
        ("get_operations_summary", "rank_regions_by_operations_metric", "get_workforce_summary", "get_truck_performance_summary", "get_environmental_summary"),
        (),
        ("incident_procedure", "operational_sop"),
        ("missed collection review and escalation procedure",),
        ("operations_outcomes", "response_guidance"),
        (
            ActionTemplate(
                ActionCategory.REVIEW_SERVICE_RECORDS,
                "Review affected service records",
                "Review the matching missed-collection records and validate their operational status.",
                ("Establish the verified incident scope."),
                ("Access to service records",),
            ),
            ActionTemplate(
                ActionCategory.ESCALATE_FOR_MANAGER_REVIEW,
                "Escalate for manager review",
                "Use available escalation guidance for authorized manager review.",
                ("Support consistent incident handling."),
                ("Applicable current procedure",),
            ),
            ActionTemplate(
                ActionCategory.REVIEW_OPERATIONAL_CAPACITY,
                "Review operational capacity",
                "Review workforce and truck evidence before considering any capacity change.",
                ("Identify evidence-supported capacity constraints without assuming causes."),
                ("Confirmed worker and truck availability",),
            ),
            ActionTemplate(
                ActionCategory.CONTINUE_MONITORING,
                "Monitor the affected region",
                "Continue monitoring when the incident count is low and no urgent condition is supported.",
                ("Track whether the condition persists."),
                ("Reliable current reporting",),
            ),
        ),
        ("incident count", "recency", "continuity risk", "known feasibility", "procedure authority"),
        ("unsupported causal attribution", "automatic reallocation"),
        ("What should we do about missed collections in Greater Cairo?",),
    )
