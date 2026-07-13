"""Parameterized pgvector cosine-similarity retrieval."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models import DocumentChunk, KnowledgeDocument
from app.retrieval._sql import evidence_columns, row_to_evidence
from app.retrieval.metadata_filters import build_metadata_conditions
from app.schemas.retrieval import RetrievalFilters, RetrievedEvidence


class VectorRetriever:
    """Search active chunks using similarity = ``1 - cosine distance``."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int,
        filters: RetrievalFilters | None = None,
        candidate_limit: int | None = None,
    ) -> list[RetrievedEvidence]:
        if len(query_embedding) != self.settings.vector_dimensions:
            raise ValueError(f"Query embedding must have {self.settings.vector_dimensions} dimensions")
        limit = max(top_k, candidate_limit or self.settings.retrieval_candidate_limit)
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        statement = (
            select(*evidence_columns(distance))
            .join(KnowledgeDocument, KnowledgeDocument.document_id == DocumentChunk.document_id)
            .where(*build_metadata_conditions(filters))
            .order_by(distance.asc(), DocumentChunk.id.asc())
            .limit(limit)
        )
        rows = (await self.session.execute(statement)).all()
        evidence = []
        for row in rows:
            similarity = max(0.0, min(1.0, 1.0 - float(row._mapping["raw_score"])))
            evidence.append(row_to_evidence(row, vector_score=similarity))
        return evidence
