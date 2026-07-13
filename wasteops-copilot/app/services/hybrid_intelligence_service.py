"""Controlled orchestration of analytics tools and existing document RAG."""

import time
import uuid

from app.analytics.enums import AnalyticsRoute
from app.retrieval.citation_builder import CitationBuilder
from app.retrieval.source_registry import cited_ids
from app.schemas.chat import RAGRequest
from app.schemas.hybrid_answer import HybridQuestionRequest, HybridQuestionResponse
from app.schemas.retrieval import RetrievalRequest
from app.prompts.registry import PromptRegistry
from app.utils.prompt_loader import load_prompt
from app.core.logging import get_logger

logger = get_logger(__name__)


class HybridIntelligenceService:
    def __init__(
        self,
        router,
        analytics_service,
        analytics_answer_service,
        rag_service,
        retrieval_service,
        context_builder,
        evidence_aggregator,
        llm_service,
        session,
        settings,
    ) -> None:
        self.router = router
        self.analytics_service = analytics_service
        self.analytics_answer_service = analytics_answer_service
        self.rag_service = rag_service
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.evidence_aggregator = evidence_aggregator
        self.llm_service = llm_service
        self.session = session
        self.settings = settings
        self.citation_builder = CitationBuilder()
        self.prompt_registry = getattr(llm_service, "prompt_registry", PromptRegistry())

    async def answer(self, request: HybridQuestionRequest) -> HybridQuestionResponse:
        request_id = uuid.uuid4()
        decision = await self.router.route(request.question)
        if decision.route == AnalyticsRoute.UNSUPPORTED:
            return HybridQuestionResponse(
                answer=load_prompt("unsupported_analytics_prompt.txt").format(reason=decision.unsupported_reason or "Unsupported request."),
                route=decision.route,
                grounded=False,
                insufficient_data=True,
                insufficient_context=True,
                database_evidence=[],
                document_citations=[],
                warnings=[decision.unsupported_reason or "Unsupported request."],
                request_id=request_id,
            )
        if decision.route == AnalyticsRoute.GENERAL_CONVERSATION:
            return HybridQuestionResponse(
                answer="I can help with WasteOps operational analytics, historical data, and documented procedures.",
                route=decision.route,
                grounded=False,
                insufficient_data=False,
                insufficient_context=False,
                database_evidence=[],
                document_citations=[],
                warnings=[],
                request_id=request_id,
            )
        if decision.route == AnalyticsRoute.DOCUMENT_KNOWLEDGE:
            rag = await self.rag_service.answer(RAGRequest(question=request.question, filters=request.document_filters, debug=request.debug))
            return HybridQuestionResponse(
                answer=rag.answer,
                route=decision.route,
                grounded=rag.grounded,
                insufficient_data=False,
                insufficient_context=rag.insufficient_context,
                database_evidence=[],
                document_citations=rag.citations,
                warnings=rag.warnings,
                request_id=request_id,
            )
        evidence = await self.analytics_service.execute(decision.tool_name, decision.parameters, self.session)
        if decision.route == AnalyticsRoute.STRUCTURED_DATA:
            analytics = await self.analytics_answer_service.answer(question=request.question, decision=decision, evidence=evidence, request_id=request_id)
            return HybridQuestionResponse(
                answer=analytics.answer,
                route=decision.route,
                grounded=analytics.grounded,
                insufficient_data=analytics.insufficient_data,
                insufficient_context=False,
                database_evidence=analytics.database_evidence,
                document_citations=[],
                warnings=analytics.warnings,
                request_id=request_id,
            )
        retrieval_started = time.perf_counter()
        retrieval = await self.retrieval_service.search(
            RetrievalRequest(
                query=decision.document_query or request.question, filters=request.document_filters, include_content=True, top_k=self.settings.retrieval_top_k
            ),
            request_id=str(request_id),
        )
        retrieval_duration = time.perf_counter() - retrieval_started
        context = self.context_builder.build(retrieval.evidence, max_tokens=self.settings.retrieval_max_context_tokens) if retrieval.evidence else None
        document_text = context.context_text if context else ""
        policy_first = any(term in request.question.casefold() for term in ("procedure", "policy", "إجراء", "سياسة")) and not any(
            term in request.question.casefold() for term in ("which", "how many", "كم", "أي")
        )
        combined, warnings = self.evidence_aggregator.aggregate(
            [evidence], document_text, max_tokens=self.settings.retrieval_max_context_tokens, policy_first=policy_first
        )
        warnings.extend(retrieval.warnings)
        if not retrieval.evidence:
            warnings.append("No relevant document evidence was found.")
        if any(item.is_synthetic for item in retrieval.evidence):
            warnings.append("The cited procedure is a synthetic demo document.")
        resolved = await self.prompt_registry.get_active_prompt("hybrid_answer")
        prompt = resolved.content.format(question=request.question, evidence=combined)
        generation_started = time.perf_counter()
        answer = await self.llm_service.generate_grounded_answer(
            system_prompt="Keep D and S evidence namespaces separate.", user_prompt=prompt, prompt_key=resolved.prompt_key, prompt_version=resolved.version
        )
        generation_duration = time.perf_counter() - generation_started
        document_citations = context.citations if context else []
        validation = self.citation_builder.validate_answer_citations(answer, document_citations)
        answer = validation.answer
        warnings.extend(validation.warnings)
        valid_d = {evidence.evidence_id}
        for citation in cited_ids(answer, "D") - valid_d:
            answer = answer.replace(f"[{citation}]", "")
            warnings.append("Invalid generated database citations were removed.")
        used_s = cited_ids(answer, "S")
        document_citations = [citation for citation in document_citations if citation.citation_id in used_s]
        grounded = bool(cited_ids(answer, "D") & valid_d or document_citations)
        logger.info(
            "hybrid_answer_completed",
            request_id=str(request_id),
            route=decision.route,
            tool_name=decision.tool_name,
            domain=decision.domain,
            database_row_count=evidence.record_count,
            no_data=self.analytics_answer_service._insufficient(evidence),
            retrieval_duration_seconds=retrieval_duration,
            generation_duration_seconds=generation_duration,
        )
        return HybridQuestionResponse(
            answer=answer.strip(),
            route=decision.route,
            grounded=grounded,
            insufficient_data=self.analytics_answer_service._insufficient(evidence),
            insufficient_context=not bool(document_citations),
            database_evidence=[evidence],
            document_citations=document_citations,
            warnings=list(dict.fromkeys(warnings)),
            request_id=request_id,
        )
