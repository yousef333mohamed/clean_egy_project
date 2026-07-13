"""Embedding batching, ordering, dimensions, and retry tests."""

from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services.embedding_service import EmbeddingResponseError, EmbeddingService


def settings(**overrides: object) -> Settings:
    values = {
        "database_url": "postgresql+asyncpg://test:test@database/test",
        "database_sync_url": "postgresql+psycopg://test:test@database/test",
        "vector_dimensions": 3,
        "embedding_batch_size": 2,
        "embedding_max_retries": 2,
    }
    values.update(overrides)
    return Settings(**values)


class FakeEmbeddings:
    def __init__(self, *, fail_once: bool = False, dimensions: int = 3) -> None:
        self.calls: list[list[str]] = []
        self.fail_once = fail_once
        self.dimensions = dimensions

    async def create(self, *, input: list[str], **_kwargs: object) -> SimpleNamespace:
        self.calls.append(input)
        if self.fail_once:
            self.fail_once = False
            raise TimeoutError("temporary")
        data = [SimpleNamespace(index=index, embedding=[float(index)] * self.dimensions) for index in reversed(range(len(input)))]
        return SimpleNamespace(data=data)


@pytest.mark.asyncio
async def test_embedding_batches_and_preserves_order() -> None:
    embeddings = FakeEmbeddings()
    service = EmbeddingService(settings(), client=SimpleNamespace(embeddings=embeddings))
    vectors = await service.embed_texts(["a", "b", "c"])
    assert embeddings.calls == [["a", "b"], ["c"]]
    assert vectors == [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]]


@pytest.mark.asyncio
async def test_dimension_mismatch_is_typed_error() -> None:
    service = EmbeddingService(settings(), client=SimpleNamespace(embeddings=FakeEmbeddings(dimensions=2)))
    with pytest.raises(EmbeddingResponseError, match="dimension mismatch"):
        await service.embed_text("text")


@pytest.mark.asyncio
async def test_retry_uses_injected_sleep() -> None:
    embeddings = FakeEmbeddings(fail_once=True)
    delays: list[int] = []

    async def sleep(delay: int) -> None:
        delays.append(delay)

    service = EmbeddingService(settings(), client=SimpleNamespace(embeddings=embeddings), sleep=sleep)
    assert len(await service.embed_text("text")) == 3
    assert len(embeddings.calls) == 2
    assert delays == [1]


@pytest.mark.asyncio
async def test_empty_embedding_input_is_rejected() -> None:
    service = EmbeddingService(settings(), client=SimpleNamespace(embeddings=FakeEmbeddings()))
    with pytest.raises(Exception, match="non-empty"):
        await service.embed_texts([])
