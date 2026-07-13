"""Report rendering service."""

from app.schemas.incident import IncidentResponse


def render_incident_markdown(report: IncidentResponse) -> str:
    """Render a validated incident response as Markdown."""
    return f"# Incident Report\n\n## Summary\n{report.summary}\n\n## Recommended Actions\n" + "\n".join(f"- {x}" for x in report.recommended_actions)
