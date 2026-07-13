"""Citation formatting."""

from app.schemas.retrieval import Evidence


def evidence_context(evidence: list[Evidence]) -> str:
    """Render numbered, source-bearing evidence for prompts."""
    return (
        "\n\n".join(f"[{i}] {item.source_type}:{item.source_name}:{item.record_reference}\n{item.content}" for i, item in enumerate(evidence, 1))
        or "No evidence was retrieved."
    )
