"""Embedding provider and document ingestion."""

from datetime import date
from hashlib import sha256
from openai import AsyncOpenAI
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.ingestion.chunker import chunk_text
from app.ingestion.document_loader import SUPPORTED_EXTENSIONS, extract_document
from app.models.document import DocumentChunk
from app.schemas.ingestion import DocumentIngestionRequest, FileIngestionSummary, IngestionSummary


class EmbeddingService:
    """OpenAI-compatible embedding client."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed text in provider-safe batches."""
        response = await self.client.embeddings.create(model=self.settings.embedding_model_name, input=texts, dimensions=self.settings.vector_dimensions)
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]


class DocumentIngestor:
    """Extract, chunk, embed, and idempotently persist documents."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.embedding_service = EmbeddingService(settings)

    async def ingest(self, request: DocumentIngestionRequest) -> IngestionSummary:
        directory = self.settings.data_dir / "documents"
        names = request.filenames or [p.name for p in directory.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS]
        results: list[FileIngestionSummary] = []
        for name in names:
            item = FileIngestionSummary(filename=name)
            results.append(item)
            path = (directory / name).resolve()
            try:
                if path.parent != directory.resolve():
                    raise ValueError("Invalid filename")
                chunks = chunk_text(extract_document(path))
                item.total_rows = len(chunks)
                vectors = await self.embedding_service.embed(chunks)
                for number, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
                    values = dict(
                        content=content,
                        content_hash=sha256(content.encode()).hexdigest(),
                        source_filename=name,
                        document_type=path.suffix.lower().lstrip("."),
                        department=request.department,
                        asset_type=request.asset_type,
                        region=request.region,
                        effective_date=date.fromisoformat(request.effective_date) if request.effective_date else None,
                        version=request.version,
                        chunk_number=number,
                        extra_metadata={},
                        embedding=vector,
                    )
                    result = await self.session.execute(insert(DocumentChunk).values(**values).on_conflict_do_nothing())
                    item.inserted_rows += int(bool(result.rowcount))
                    item.duplicate_rows += int(not result.rowcount)
                await self.session.commit()
            except Exception as exc:
                await self.session.rollback()
                item.failed_rows = max(1, item.total_rows - item.inserted_rows - item.duplicate_rows)
                item.errors.append(str(exc))
        return IngestionSummary(
            files=results,
            inserted_rows=sum(x.inserted_rows for x in results),
            duplicate_rows=sum(x.duplicate_rows for x in results),
            failed_rows=sum(x.failed_rows for x in results),
        )
