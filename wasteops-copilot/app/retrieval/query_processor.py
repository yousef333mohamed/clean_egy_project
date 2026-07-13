"""Deterministic multilingual query normalization and optional rewriting."""

import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import Settings, get_settings
from app.ingestion.text_cleaner import detect_language
from app.schemas.retrieval import ProcessedQuery, QueryEntities


class QueryProcessingError(ValueError):
    """A user query cannot be processed safely."""


class QueryRewrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rewritten_query: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    document_types: list[str] = Field(default_factory=list)
    asset_types: list[str] = Field(default_factory=list)


class QueryProcessor:
    """Preserve the original question while producing retrieval-safe metadata."""

    def __init__(self, settings: Settings | None = None, *, rewriter: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self.rewriter = rewriter

    @staticmethod
    def _entities(query: str) -> QueryEntities:
        def matches(prefix: str) -> list[str]:
            return list(dict.fromkeys(re.findall(rf"\b{prefix}-[\w\u0600-\u06ff-]+", query, flags=re.IGNORECASE)))

        known_regions = [
            region for region in ("Greater Cairo", "Upper Egypt", "Lower Egypt", "القاهرة", "الجيزة", "أسوان") if region.casefold() in query.casefold()
        ]
        return QueryEntities(
            bin_ids=matches("BIN"),
            truck_ids=matches("TRK"),
            worker_ids=matches("(?:WRK|WORKER)"),
            policy_codes=matches("(?:POL|SOP|CODE)"),
            regions=known_regions,
            dates=list(dict.fromkeys(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", query))),
        )

    @staticmethod
    def _ambiguous(query: str) -> bool:
        words = query.split()
        conversational = re.search(r"\b(can you|could you|tell me|help me|what about)\b", query, re.IGNORECASE)
        return len(words) <= 4 or conversational is not None

    async def process(self, query: str) -> ProcessedQuery:
        original = query
        normalized = re.sub(r"\s+", " ", query).strip()
        if not normalized:
            raise QueryProcessingError("Question must not be empty")
        if len(normalized) > self.settings.retrieval_max_query_chars:
            raise QueryProcessingError(f"Question exceeds {self.settings.retrieval_max_query_chars} characters")
        rewritten: str | None = None
        hints: dict[str, list[str]] = {}
        if self.settings.retrieval_enable_query_rewrite and self.rewriter is not None and self._ambiguous(normalized):
            try:
                raw = await self.rewriter.rewrite_query(normalized)
                if isinstance(raw, str):
                    raw = json.loads(raw)
                parsed = QueryRewrite.model_validate(raw)
                identifiers = self._entities(normalized)
                required = identifiers.bin_ids + identifiers.truck_ids + identifiers.worker_ids + identifiers.dates
                if not all(identifier in parsed.rewritten_query for identifier in required):
                    raise QueryProcessingError("Rewrite did not preserve identifiers and dates")
                rewritten = re.sub(r"\s+", " ", parsed.rewritten_query).strip()
                hints = {
                    "keywords": parsed.keywords,
                    "document_types": parsed.document_types,
                    "asset_types": parsed.asset_types,
                }
            except (Exception, ValidationError, json.JSONDecodeError):
                rewritten = None
                hints = {}
        return ProcessedQuery(
            original_query=original,
            normalized_query=normalized,
            rewritten_query=rewritten,
            language=detect_language(normalized),
            entities=self._entities(normalized),
            rewrite_hints=hints,
        )
