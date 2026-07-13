"""Small dependency assembly helpers for API and CLI entry points."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.retrieval.context_builder import ContextBuilder
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.keyword_retriever import KeywordRetriever
from app.retrieval.query_processor import QueryProcessor
from app.retrieval.reranker import EvidenceReranker
from app.retrieval.retrieval_service import RetrievalService
from app.retrieval.vector_retriever import VectorRetriever
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.prompts.registry import PromptRegistry
from app.observability.tracer import Tracer
from app.utils.token_counter import TokenCounter


def build_retrieval_service(
    session: AsyncSession,
    settings: Settings,
    *,
    embedding_service=None,
    query_rewriter=None,
) -> RetrievalService:
    """Assemble retrieval components while keeping each independently testable."""
    vector = VectorRetriever(session, settings)
    keyword = KeywordRetriever(session, settings)
    hybrid = HybridRetriever(vector, keyword, settings)
    return RetrievalService(
        QueryProcessor(settings, rewriter=query_rewriter),
        embedding_service or EmbeddingService(settings),
        hybrid,
        EvidenceReranker(),
        settings,
        tracer=Tracer(session, settings),
    )


def build_rag_service(session: AsyncSession, settings: Settings) -> RAGService:
    """Assemble one request-scoped RAG service and shared chat adapter."""
    llm = LLMService(settings, prompt_registry=PromptRegistry(session), tracer=Tracer(session, settings))
    retrieval = build_retrieval_service(
        session,
        settings,
        query_rewriter=llm if settings.retrieval_enable_query_rewrite else None,
    )
    context = ContextBuilder(TokenCounter(settings.chat_model_name))
    return RAGService(retrieval, context, llm, settings)
