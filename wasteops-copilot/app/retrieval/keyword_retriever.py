"""PostgreSQL full-text retrieval with safe multilingual token fallback."""

import re

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models import DocumentChunk, KnowledgeDocument
from app.retrieval._sql import evidence_columns, row_to_evidence
from app.retrieval.metadata_filters import build_metadata_conditions
from app.schemas.retrieval import RetrievalFilters, RetrievedEvidence

STOP_WORDS = frozenset({"a", "an", "and", "are", "is", "of", "or", "the", "to", "what", "when", "في", "من", "ما", "هو", "و"})


def keyword_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[\w\u0600-\u06ff-]+", query, flags=re.UNICODE)
    return list(dict.fromkeys(token for token in tokens if len(token) > 1 and token.casefold() not in STOP_WORDS))[:12]


class KeywordRetriever:
    """Use ``simple`` FTS plus ILIKE because Arabic stemming is not configured."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def search(
        self,
        query: str,
        *,
        top_k: int,
        filters: RetrievalFilters | None = None,
        candidate_limit: int | None = None,
    ) -> list[RetrievedEvidence]:
        tokens = keyword_tokens(query)
        if not tokens:
            return []
        limit = max(top_k, candidate_limit or self.settings.retrieval_candidate_limit)
        vector = func.to_tsvector("simple", func.coalesce(DocumentChunk.content, ""))
        ts_query = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank_cd(vector, ts_query)
        searchable = func.concat_ws(
            " ",
            DocumentChunk.content,
            DocumentChunk.section_title,
            DocumentChunk.source_filename,
            DocumentChunk.document_type,
            DocumentChunk.asset_type,
        )
        token_matches = [cast(searchable, String).ilike(f"%{token}%") for token in tokens]
        statement = (
            select(*evidence_columns(rank))
            .join(KnowledgeDocument, KnowledgeDocument.document_id == DocumentChunk.document_id)
            .where(*build_metadata_conditions(filters), or_(vector.op("@@")(ts_query), *token_matches))
            .order_by(rank.desc(), DocumentChunk.id.asc())
            .limit(limit)
        )
        rows = (await self.session.execute(statement)).all()
        results: list[RetrievedEvidence] = []
        identifiers = [token for token in tokens if re.match(r"^(BIN|TRK|WRK|SOP|POL|CODE)-", token, re.IGNORECASE)]
        for row in rows:
            content = row._mapping["content"]
            coverage = sum(token.casefold() in content.casefold() for token in tokens) / len(tokens)
            raw_rank = max(0.0, float(row._mapping["raw_score"] or 0))
            normalized_rank = raw_rank / (raw_rank + 1.0)
            exact = 1.0 if identifiers and any(identifier.casefold() in content.casefold() for identifier in identifiers) else 0.0
            score = min(1.0, 0.65 * coverage + 0.25 * normalized_rank + 0.10 * exact)
            results.append(row_to_evidence(row, keyword_score=score))
        return sorted(results, key=lambda item: (-item.keyword_score, item.chunk_id))
