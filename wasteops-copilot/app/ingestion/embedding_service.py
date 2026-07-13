"""Backward-compatible ingestion namespace for the embedding adapter."""

from app.services.embedding_service import EmbeddingConfigurationError, EmbeddingError, EmbeddingResponseError, EmbeddingService

__all__ = ["EmbeddingConfigurationError", "EmbeddingError", "EmbeddingResponseError", "EmbeddingService"]
