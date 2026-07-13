"""Request-scoped assembly for analytics and hybrid intelligence."""

from app.analytics.analytics_service import AnalyticsService
from app.analytics.tool_registry import build_tool_registry
from app.retrieval.context_builder import ContextBuilder
from app.retrieval.evidence_aggregator import EvidenceAggregator
from app.retrieval.factory import build_retrieval_service
from app.services.analytics_answer_service import AnalyticsAnswerService
from app.services.analytics_router_service import AnalyticsRouterService
from app.services.hybrid_intelligence_service import HybridIntelligenceService
from app.services.llm_service import LLMConfigurationError, LLMService
from app.services.rag_service import RAGService
from app.utils.token_counter import TokenCounter
from app.prompts.registry import PromptRegistry
from app.observability.tracer import Tracer


def build_analytics_stack(session, settings):
    registry = build_tool_registry(settings)
    try:
        llm = LLMService(settings, prompt_registry=PromptRegistry(session), tracer=Tracer(session, settings))
    except LLMConfigurationError:
        llm = None
    router = AnalyticsRouterService(registry, settings, llm_service=llm)
    analytics = AnalyticsService(registry, settings, tracer=Tracer(session, settings))
    answer = AnalyticsAnswerService(llm)
    return registry, router, analytics, answer, llm


def build_hybrid_service(session, settings) -> HybridIntelligenceService:
    registry, router, analytics, answer, llm = build_analytics_stack(session, settings)
    if llm is None:
        raise LLMConfigurationError("LLM_API_KEY is required for hybrid answers")
    retrieval = build_retrieval_service(session, settings, query_rewriter=llm if settings.retrieval_enable_query_rewrite else None)
    counter = TokenCounter(settings.chat_model_name)
    context = ContextBuilder(counter)
    rag = RAGService(retrieval, context, llm, settings)
    return HybridIntelligenceService(router, analytics, answer, rag, retrieval, context, EvidenceAggregator(counter), llm, session, settings)
