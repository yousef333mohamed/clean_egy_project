"""Intent-aware hybrid retrieval orchestration."""

from app.retrieval.intent_router import IntentRouter
from app.retrieval.sql_retriever import SQLRetriever
from app.retrieval.vector_retriever import VectorRetriever
from app.schemas.retrieval import Evidence, IntentResult


class HybridRetriever:
    """Combine exact SQL facts with semantic document context."""

    def __init__(self, router: IntentRouter, sql: SQLRetriever, vector: VectorRetriever) -> None:
        self.router = router
        self.sql = sql
        self.vector = vector

    async def retrieve(self, question: str) -> tuple[IntentResult, list[Evidence]]:
        """Route and retrieve required evidence types."""
        route = await self.router.route(question)
        evidence: list[Evidence] = []
        if route.requires_sql:
            evidence.extend(await self.sql.retrieve(question))
        if route.requires_vector_search:
            evidence.extend(await self.vector.retrieve(question))
        evidence.sort(key=lambda x: x.relevance_score, reverse=True)
        return route, evidence
