"""pgvector semantic retrieval."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.ingestion.embeddings import EmbeddingService
from app.models.document import DocumentChunk
from app.schemas.retrieval import Evidence


class VectorRetriever:
    """Retrieve semantically similar document chunks."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.embeddings = EmbeddingService(settings)

    async def retrieve(self, question: str) -> list[Evidence]:
        """Embed a query and return nearest document chunks."""
        if not self.settings.llm_api_key:
            return []
        vector = (await self.embeddings.embed([question]))[0]
        distance = DocumentChunk.embedding.cosine_distance(vector).label("distance")
        rows = (await self.session.execute(select(DocumentChunk, distance).order_by(distance).limit(self.settings.retrieval_top_k))).all()
        return [
            Evidence(
                content=chunk.content,
                source_type="document",
                source_name=chunk.source_filename,
                record_reference=f"chunk:{chunk.chunk_number}",
                relevance_score=max(0.0, min(1.0, 1.0 - float(dist))),
            )
            for chunk, dist in rows
        ]
