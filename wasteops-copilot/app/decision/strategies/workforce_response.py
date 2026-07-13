"""Workforce operational-response definition."""

from app.decision.decision_registry import ActionTemplate, DecisionDefinition
from app.decision.enums import ActionCategory, DecisionType


def definition() -> DecisionDefinition:
    return DecisionDefinition(
        DecisionType.WORKFORCE_OPERATIONAL_RESPONSE,
        "Review workforce coverage and workload without employment or disciplinary decisions.",
        ("get_workforce_summary", "rank_workforce_groups"),
        (),
        ("operational_sop",),
        ("workforce coverage and supervisory review procedure",),
        ("attendance_coverage", "workload_evidence"),
        (
            ActionTemplate(
                ActionCategory.REVIEW_ATTENDANCE_COVERAGE,
                "Review attendance coverage",
                "Review attendance coverage for the requested scope before considering assignments.",
                "Identify coverage gaps for supervisory review.",
                "Confirmed shift requirements and worker availability",
            ),
            ActionTemplate(
                ActionCategory.REVIEW_WORKLOAD_DISTRIBUTION,
                "Review workload distribution",
                "Review task distribution across the supported grouping without making employment decisions.",
                "Identify uneven historical workload for manager assessment.",
                "Current operational requirements",
            ),
            ActionTemplate(
                ActionCategory.REVIEW_OVERTIME,
                "Review overtime concentration",
                "Review groups with concentrated overtime and verify the underlying records.",
                "Support service continuity while monitoring workload risk.",
                "Complete attendance records",
            ),
            ActionTemplate(
                ActionCategory.ESCALATE_FOR_MANAGER_REVIEW,
                "Request supervisory review",
                "Request additional supervisory review when evidence indicates coverage concerns.",
                "Place decisions with an authorized manager.",
                "Supervisor availability",
            ),
            ActionTemplate(
                ActionCategory.CONTINUE_MONITORING,
                "Continue monitoring",
                "Continue monitoring when attendance and workload evidence shows no supported concern.",
                "Avoid unsupported workforce intervention.",
                "Current attendance reporting",
            ),
        ),
        ("coverage", "operational urgency", "continuity", "known feasibility", "procedure authority"),
        ("disciplinary action", "automatic worker assignment"),
        ("How should we respond to workforce absence?",),
    )
