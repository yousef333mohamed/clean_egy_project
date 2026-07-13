"""OpenAI-compatible, batched embedding service with explicit retries."""

import asyncio
from typing import Any

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingError(RuntimeError):
    """Base exception for safe embedding failures."""


class EmbeddingConfigurationError(EmbeddingError):
    """Embedding credentials or settings are missing."""


class EmbeddingResponseError(EmbeddingError):
    """The provider returned an invalid or incompatible response."""


class EmbeddingService:
    """Create embeddings without logging source content or credentials."""

    def __init__(self, settings: Settings | None = None, *, client: Any | None = None, sleep: Any = asyncio.sleep) -> None:
        self.settings = settings or get_settings()
        if client is None:
            if not self.settings.llm_api_key:
                raise EmbeddingConfigurationError("LLM_API_KEY is required for document embedding")
            client = AsyncOpenAI(
                api_key=self.settings.llm_api_key,
                base_url=self.settings.llm_base_url,
                timeout=self.settings.embedding_timeout_seconds,
                max_retries=0,
            )
        self.client = client
        self.sleep = sleep

    async def embed_text(self, text: str) -> list[float]:
        """Embed exactly one non-empty text value."""
        return (await self.embed_texts([text]))[0]

    async def _request(self, texts: list[str]) -> list[list[float]]:
        last_error: Exception | None = None
        for attempt in range(self.settings.embedding_max_retries + 1):
            try:
                logger.info(
                    "embedding_request",
                    model=self.settings.embedding_model_name,
                    batch_size=len(texts),
                    attempt=attempt + 1,
                )
                response = await self.client.embeddings.create(
                    model=self.settings.embedding_model_name,
                    input=texts,
                    dimensions=self.settings.vector_dimensions,
                    timeout=self.settings.embedding_timeout_seconds,
                )
                ordered = sorted(response.data, key=lambda item: item.index)
                if len(ordered) != len(texts):
                    raise EmbeddingResponseError("Embedding response count did not match request count")
                vectors = [list(item.embedding) for item in ordered]
                if any(len(vector) != self.settings.vector_dimensions for vector in vectors):
                    raise EmbeddingResponseError(f"Embedding dimension mismatch; expected {self.settings.vector_dimensions}")
                return vectors
            except EmbeddingResponseError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "embedding_request_failed",
                    model=self.settings.embedding_model_name,
                    batch_size=len(texts),
                    attempt=attempt + 1,
                    error_type=type(exc).__name__,
                )
                if attempt >= self.settings.embedding_max_retries:
                    break
                await self.sleep(2**attempt)
        raise EmbeddingError(f"Embedding request failed after retries: {type(last_error).__name__}") from last_error

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in configured batches while preserving input order."""
        if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
            raise EmbeddingError("Embedding input must contain non-empty text values")
        vectors: list[list[float]] = []
        size = self.settings.embedding_batch_size
        for offset in range(0, len(texts), size):
            vectors.extend(await self._request(texts[offset : offset + size]))
        return vectors
