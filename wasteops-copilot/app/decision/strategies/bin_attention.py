"""Bin-attention decision definition."""

from app.decision.decision_registry import ActionTemplate, DecisionDefinition
from app.decision.enums import ActionCategory, DecisionType


def definition() -> DecisionDefinition:
    return DecisionDefinition(
        DecisionType.BIN_ATTENTION_PRIORITY,
        "Prioritize latest critical-fill, fault, and low-battery bin conditions for manager review.",
        ("list_critical_bins", "list_low_battery_bins", "list_sensor_fault_bins", "get_bin_status_summary", "get_operations_summary"),
        (),
        ("operational_sop", "maintenance_manual"),
        ("critical bin collection and sensor maintenance procedure",),
        ("latest_bin_status", "configured_rules"),
        (
            ActionTemplate(
                ActionCategory.PRIORITIZE_COLLECTION_REVIEW,
                "Review critical-fill bins",
                "Prioritize the returned critical-fill bins for operational review; do not schedule collection automatically.",
                ("Protect service continuity by reviewing current critical conditions."),
                ("Manager confirmation of collection capacity",),
            ),
            ActionTemplate(
                ActionCategory.REQUEST_INSPECTION,
                "Inspect current sensor faults",
                "Request maintenance inspection of bins whose latest sensor status is faulty.",
                ("Validate whether current telemetry is reliable."),
                ("Qualified maintenance review",),
            ),
            ActionTemplate(
                ActionCategory.REQUEST_BATTERY_REPLACEMENT,
                "Review low-battery bins",
                "Request preventive battery review for bins below the configured threshold.",
                ("Reduce risk of telemetry interruption."),
                ("Battery stock and technician availability must be confirmed",),
            ),
            ActionTemplate(
                ActionCategory.COMBINED_OPERATIONAL_REVIEW,
                "Combine collection and maintenance review",
                "Review urgent collection and maintenance conditions together before assigning resources.",
                ("Coordinate service-continuity and equipment concerns."),
                ("Manager prioritization and resource confirmation",),
            ),
            ActionTemplate(
                ActionCategory.CONTINUE_MONITORING,
                "Continue monitoring",
                "Continue monitoring when no current urgent condition is supported by evidence.",
                ("Avoid unnecessary intervention when no condition is present."),
                ("Reliable incoming telemetry",),
            ),
        ),
        ("service impact", "urgency", "risk control", "feasibility", "policy alignment"),
        ("future overflow prediction", "automatic collection scheduling"),
        ("Which bins require immediate attention?",),
    )
