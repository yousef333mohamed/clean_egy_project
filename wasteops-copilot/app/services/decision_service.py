"""Evidence-grounded operational decision service."""

from typing import Protocol
from app.retrieval.citation_builder import evidence_context
from app.retrieval.hybrid_retriever import HybridRetriever
from app.schemas.decision import DecisionResponse
from app.schemas.retrieval import Evidence
from app.services.llm_service import LLMService


class PredictionGateway(Protocol):
    """Future Data Science API boundary."""

    async def predict_bin_overflow(self, payload: dict) -> dict: ...
    async def calculate_collection_priority(self, payload: dict) -> dict: ...
    async def detect_truck_anomaly(self, payload: dict) -> dict: ...
    async def predict_missed_collection(self, payload: dict) -> dict: ...
    async def forecast_workforce_requirement(self, payload: dict) -> dict: ...


def calculate_confidence(evidence: list[Evidence], missing_count: int) -> float:
    """Calculate confidence from coverage, relevance, completeness, and source agreement."""
    if not evidence:
        return 0.0
    coverage = min(1.0, len(evidence) / 5)
    relevance = sum(e.relevance_score for e in evidence) / len(evidence)
    completeness = max(0.0, 1.0 - missing_count / 5)
    types = {e.source_type for e in evidence}
    agreement = 1.0 if len(types) > 1 else 0.65
    return round(0.30 * coverage + 0.35 * relevance + 0.20 * completeness + 0.15 * agreement, 2)


class DecisionService:
    """Produce a grounded recommendation with deterministic confidence."""

    def __init__(self, retriever: HybridRetriever, llm: LLMService) -> None:
        self.retriever = retriever
        self.llm = llm

    async def recommend(self, question: str) -> DecisionResponse:
        """Retrieve evidence and ask the model for an operational decision."""
        _, evidence = await self.retriever.retrieve(question)
        if not evidence:
            return DecisionResponse(
                situation_summary="Insufficient evidence was retrieved.",
                recommended_decision="Collect the missing operational data before making a decision.",
                supporting_evidence=[],
                expected_impact={},
                risks=["Acting without evidence may degrade service."],
                alternative_decisions=["Escalate for manual review."],
                confidence_score=0,
                missing_information=["Relevant operational records or procedures"],
                retrieved_facts=[],
                model_assumptions=[],
            )
        response = await self.llm.structured(
            self.llm.prompt("decision_prompt.txt"), f"Question: {question}\nEvidence:\n{evidence_context(evidence)}", DecisionResponse
        )
        response.supporting_evidence = evidence
        response.confidence_score = calculate_confidence(evidence, len(response.missing_information))
        return response
