"""Request-scoped assembly for decision preview and recommendation services."""

from app.analytics.analytics_service import AnalyticsService
from app.analytics.tool_registry import build_tool_registry
from app.decision.confidence_calculator import ConfidenceCalculator
from app.decision.context_planner import DecisionContextPlanner
from app.decision.decision_registry import build_decision_registry
from app.decision.decision_router import DecisionRouter
from app.decision.evidence_collector import DecisionEvidenceCollector
from app.decision.option_generator import OptionGenerator
from app.decision.option_scorer import OptionScorer
from app.decision.risk_analyzer import RiskAnalyzer
from app.retrieval.context_builder import ContextBuilder
from app.retrieval.factory import build_retrieval_service
from app.services.embedding_service import EmbeddingConfigurationError, EmbeddingService
from app.services.llm_service import LLMConfigurationError, LLMService
from app.services.decision_intelligence_service import DecisionIntelligenceService
from app.utils.token_counter import TokenCounter


class _UnavailableEmbedding:
    async def embed_text(self, _text):
        raise EmbeddingConfigurationError("LLM_API_KEY is required for document retrieval")


def build_decision_preview(settings):
    decision_registry = build_decision_registry()
    analytics_registry = build_tool_registry(settings)
    try:
        llm = LLMService(settings)
    except LLMConfigurationError:
        llm = None
    router = DecisionRouter(decision_registry, analytics_registry, llm_service=llm)
    planner = DecisionContextPlanner(decision_registry, analytics_registry, settings)
    return decision_registry, analytics_registry, router, planner, llm


def build_decision_service(session, settings) -> DecisionIntelligenceService:
    decision_registry, analytics_registry, router, planner, llm = build_decision_preview(settings)
    try:
        embedding = EmbeddingService(settings)
    except EmbeddingConfigurationError:
        embedding = _UnavailableEmbedding()
    retrieval = build_retrieval_service(
        session,
        settings,
        embedding_service=embedding,
        query_rewriter=llm if llm and settings.retrieval_enable_query_rewrite else None,
    )
    context = ContextBuilder(TokenCounter(settings.chat_model_name))
    analytics = AnalyticsService(analytics_registry, settings)
    collector = DecisionEvidenceCollector(analytics, retrieval, context, session, settings)
    return DecisionIntelligenceService(
        router,
        planner,
        collector,
        OptionGenerator(decision_registry, settings),
        OptionScorer(settings),
        ConfidenceCalculator(settings),
        RiskAnalyzer(),
        decision_registry,
        settings,
        llm_service=llm,
    )
