"""Incident investigation service."""

from app.retrieval.citation_builder import evidence_context
from app.retrieval.hybrid_retriever import HybridRetriever
from app.schemas.incident import IncidentResponse
from app.services.llm_service import LLMService


class IncidentService:
    """Investigate incidents without overstating causation."""

    def __init__(self, retriever: HybridRetriever, llm: LLMService) -> None:
        self.retriever = retriever
        self.llm = llm

    async def investigate(self, question: str) -> IncidentResponse:
        _, evidence = await self.retriever.retrieve(question)
        if not evidence:
            return IncidentResponse(
                summary="No relevant evidence was retrieved.",
                timeline=[],
                probable_factors=[],
                recommended_actions=["Collect incident records and telemetry."],
                evidence=[],
                missing_information=["Incident evidence"],
            )
        result = await self.llm.structured(
            self.llm.prompt("incident_report_prompt.txt"), f"Question: {question}\nEvidence:\n{evidence_context(evidence)}", IncidentResponse
        )
        result.evidence = evidence
        return result
