"""Truck-performance response definition."""

from app.decision.decision_registry import ActionTemplate, DecisionDefinition
from app.decision.enums import ActionCategory, DecisionType


def definition() -> DecisionDefinition:
    return DecisionDefinition(
        DecisionType.TRUCK_PERFORMANCE_RESPONSE,
        "Review historical truck performance and deterministic anomaly rules without removing vehicles from service.",
        ("get_truck_performance_summary", "rank_trucks_by_metric", "detect_truck_rule_anomalies"),
        (),
        ("maintenance_manual", "operational_sop"),
        ("truck fuel anomaly pre-trip inspection procedure",),
        ("truck_performance", "rule_anomalies", "inspection_guidance"),
        (
            ActionTemplate(
                ActionCategory.REQUEST_INSPECTION,
                "Request truck inspection",
                "Request an authorized inspection based on the returned rule anomaly without changing the truck's service status.",
                "Validate equipment condition before further management action.",
                "Authorized inspector and vehicle availability must be confirmed",
            ),
            ActionTemplate(
                ActionCategory.REVIEW_FUEL_RECORDS,
                "Review fuel records",
                "Review source fuel records and reconcile the trips that triggered configured fuel rules.",
                "Validate whether the recorded consumption is accurate.",
                "Fuel logs and trip records",
            ),
            ActionTemplate(
                ActionCategory.REVIEW_LOAD_AND_DURATION,
                "Review load and duration",
                "Review load, distance, and duration records together for the affected trips.",
                "Identify record-level conditions requiring investigation without claiming a cause.",
                "Complete trip records",
            ),
            ActionTemplate(
                ActionCategory.ESCALATE_FOR_MANAGER_REVIEW,
                "Flag for manager review",
                "Temporarily flag the evidence for manager review without changing truck status.",
                "Ensure an accountable review of persistent anomalies.",
                "Authorized manager decision",
            ),
            ActionTemplate(
                ActionCategory.CONTINUE_MONITORING,
                "Monitor subsequent trips",
                "Monitor subsequent trips when no deterministic anomaly is present.",
                "Avoid unsupported intervention while retaining oversight.",
                "Future trip records",
            ),
        ),
        ("affected trips", "rule urgency", "equipment-risk control", "known inspection feasibility", "manual authority"),
        ("automatic truck removal", "machine-learning anomaly claims"),
        ("Should TRK-014 be inspected?",),
    )
