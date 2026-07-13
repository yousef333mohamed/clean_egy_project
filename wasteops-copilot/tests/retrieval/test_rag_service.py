"""Grounded, insufficient-context, citation, authority, and provider tests."""

import pytest

from app.core.config import Settings
from app.retrieval.context_builder import ContextBuilder
from app.schemas.chat import RAGRequest
from app.schemas.retrieval import RetrievalResponse
from app.services.llm_service import LLMError
from app.services.rag_service import RAGService
from app.utils.token_counter import TokenCounter


def settings():
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        retrieval_enable_query_rewrite=False,
    )


class Retrieval:
    def __init__(self, evidence):
        self.evidence = evidence

    async def search(self, request, **_kwargs):
        return RetrievalResponse(
            query=request.query,
            rewritten_query=None,
            language="ar" if "حساس" in request.query else "en",
            evidence=self.evidence,
            filters_applied=request.filters.applied() if request.filters else {},
        )


class LLM:
    def __init__(self, answer="Inspect and escalate [S1]."):
        self.answer_text = answer
        self.calls = 0

    async def generate_grounded_answer(self, **_kwargs):
        self.calls += 1
        return self.answer_text


@pytest.mark.asyncio
async def test_successful_grounded_answer_and_synthetic_warning(evidence_factory) -> None:
    llm = LLM()
    service = RAGService(Retrieval([evidence_factory()]), ContextBuilder(TokenCounter("gpt-4.1-mini")), llm, settings())
    response = await service.answer(RAGRequest(question="What is the sensor procedure?"))
    assert response.grounded is True
    assert response.citations[0].citation_id == "S1"
    assert response.request_id
    assert any("synthetic" in warning.lower() for warning in response.warnings)
    assert llm.calls == 1


@pytest.mark.asyncio
async def test_no_evidence_returns_insufficient_without_llm() -> None:
    llm = LLM()
    service = RAGService(Retrieval([]), ContextBuilder(TokenCounter("gpt-4.1-mini")), llm, settings())
    response = await service.answer(RAGRequest(question="Unsupported corporate policy?"))
    assert response.insufficient_context is True
    assert response.citations == []
    assert llm.calls == 0


@pytest.mark.asyncio
async def test_invalid_model_citation_is_removed(evidence_factory) -> None:
    llm = LLM("Use the procedure [S9].")
    service = RAGService(Retrieval([evidence_factory()]), ContextBuilder(TokenCounter("gpt-4.1-mini")), llm, settings())
    response = await service.answer(RAGRequest(question="sensor"))
    assert "[S9]" not in response.answer
    assert response.grounded is False
    assert response.warnings


@pytest.mark.asyncio
async def test_llm_provider_failure_propagates(evidence_factory) -> None:
    class Failed:
        async def generate_grounded_answer(self, **_kwargs):
            raise LLMError("offline")

    service = RAGService(Retrieval([evidence_factory()]), ContextBuilder(TokenCounter("gpt-4.1-mini")), Failed(), settings())
    with pytest.raises(LLMError):
        await service.answer(RAGRequest(question="ما إجراء حساس الحاوية؟"))
