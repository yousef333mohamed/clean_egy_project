"""Sensor-maintenance response definition."""

from app.decision.decision_registry import ActionTemplate, DecisionDefinition
from app.decision.enums import ActionCategory, DecisionType


def definition() -> DecisionDefinition:
    return DecisionDefinition(
        DecisionType.SENSOR_MAINTENANCE_RESPONSE,
        "Respond to latest sensor faults and low-battery conditions without automatic maintenance actions.",
        ("list_sensor_fault_bins", "list_low_battery_bins", "get_bin_status_summary"),
        (),
        ("maintenance_manual", "operational_sop"),
        ("sensor maintenance fault battery connectivity inspection procedure",),
        ("latest_sensor_status", "maintenance_guidance", "configured_rules"),
        (
            ActionTemplate(
                ActionCategory.REQUEST_INSPECTION,
                "Request sensor inspection",
                "Request inspection of bins with a current fault status.",
                ("Validate the fault and telemetry reliability."),
                ("Qualified technician availability",),
            ),
            ActionTemplate(
                ActionCategory.REQUEST_BATTERY_REPLACEMENT,
                "Request battery review",
                "Request battery inspection or replacement review for current low-battery bins.",
                ("Reduce telemetry interruption risk."),
                ("Confirmed compatible battery and technician",),
            ),
            ActionTemplate(
                ActionCategory.VALIDATE_CONNECTIVITY,
                "Validate connectivity",
                "Validate device communication before concluding that hardware replacement is required.",
                ("Distinguish communication issues from device faults."),
                ("Connectivity diagnostics",),
            ),
            ActionTemplate(
                ActionCategory.ESCALATE_FOR_MANAGER_REVIEW,
                "Escalate unresolved faults",
                "Escalate faults that remain unresolved after inspection according to available guidance.",
                ("Avoid leaving persistent telemetry failures unresolved."),
                ("Applicable escalation procedure",),
            ),
            ActionTemplate(
                ActionCategory.CONTINUE_MONITORING,
                "Continue monitoring",
                "Continue monitoring when the latest status is healthy.",
                ("Avoid unnecessary maintenance."),
                ("Reliable telemetry",),
            ),
        ),
        ("fault count", "current status", "failure prevention", "inspection feasibility", "manual authority"),
        ("automatic maintenance completion",),
        ("What action should we take for faulty sensors?",),
    )
