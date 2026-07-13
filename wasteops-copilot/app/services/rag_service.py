"""First grounded WasteOps RAG answer workflow."""

import time
import uuid
from datetime import date

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.retrieval.citation_builder import CitationBuilder
from app.schemas.chat import RAGRequest, RAGResponse
from app.schemas.retrieval import RetrievalRequest
from app.utils.prompt_loader import load_prompt

logger = get_logger(__name__)


class RAGService:
    """Generate answers only from retrieved, delimited, citation-mapped evidence."""

    def __init__(self, retrieval_service, context_builder, llm_service, settings: Settings | None = None) -> None:
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.llm_service = llm_service
        self.settings = settings or get_settings()
        self.citation_builder = CitationBuilder()

    @staticmethod
    def _authority_warnings(evidence) -> list[str]:
        warnings = []
        today = date.today()
        if any(item.is_synthetic for item in evidence):
            warnings.append("Recommendations rely on synthetic demo documents and are not official company policy.")
        if any(item.authority_level == "unknown" for item in evidence):
            warnings.append("Some evidence has unknown authority and should be verified before operational use.")
        if any(item.expiration_date and item.expiration_date < today for item in evidence):
            warnings.append("Some evidence is expired and may be outdated.")
        elif any(item.effective_date and today.year - item.effective_date.year > 5 for item in evidence):
            warnings.append("Some evidence has an old effective date and may be outdated.")
        if any(not item.version for item in evidence):
            warnings.append("Some evidence has no version metadata.")
        return warnings

    async def answer(self, request: RAGRequest) -> RAGResponse:
        request_id = uuid.uuid4()
        debug_enabled = request.debug and self.settings.enable_retrieval_debug_api
        retrieval = await self.retrieval_service.search(
            RetrievalRequest(
                query=request.question,
                top_k=request.top_k,
                filters=request.filters,
                include_content=True,
                debug=debug_enabled,
            ),
            request_id=str(request_id),
        )
        warnings = list(retrieval.warnings)
        warnings.extend(self._authority_warnings(retrieval.evidence))
        if not retrieval.evidence:
            warnings.append("No evidence met the configured retrieval score threshold.")
            return RAGResponse(
                answer=load_prompt("no_context_response.txt"),
                grounded=False,
                insufficient_context=True,
                citations=[],
                retrieved_evidence_count=0,
                used_evidence_count=0,
                warnings=list(dict.fromkeys(warnings)),
                query=retrieval.query,
                rewritten_query=retrieval.rewritten_query,
                filters_applied=retrieval.filters_applied,
                request_id=request_id,
                debug=retrieval.debug if debug_enabled else None,
            )
        context = self.context_builder.build(
            retrieval.evidence,
            max_tokens=self.settings.retrieval_max_context_tokens,
        )
        warnings.extend(context.warnings)
        if not context.included_chunk_ids:
            warnings.append("Evidence could not fit within the configured context-token budget.")
            return RAGResponse(
                answer=load_prompt("no_context_response.txt"),
                grounded=False,
                insufficient_context=True,
                citations=[],
                retrieved_evidence_count=len(retrieval.evidence),
                used_evidence_count=0,
                warnings=list(dict.fromkeys(warnings)),
                query=retrieval.query,
                rewritten_query=retrieval.rewritten_query,
                filters_applied=retrieval.filters_applied,
                request_id=request_id,
                debug=retrieval.debug if debug_enabled else None,
            )
        system_prompt = load_prompt("rag_system_prompt.txt")
        user_prompt = load_prompt("rag_answer_prompt.txt").format(question=retrieval.query, context=context.context_text)
        generation_started = time.perf_counter()
        answer = await self.llm_service.generate_grounded_answer(system_prompt=system_prompt, user_prompt=user_prompt)
        generation_duration = time.perf_counter() - generation_started
        validation = self.citation_builder.validate_answer_citations(answer, context.citations)
        warnings.extend(validation.warnings)
        debug = retrieval.debug.copy() if debug_enabled and retrieval.debug else None
        if debug is not None:
            debug.update(
                {
                    "context_tokens": context.estimated_tokens,
                    "context_truncated": context.truncated,
                    "generation_duration_seconds": generation_duration,
                }
            )
        grounded = bool(validation.citations)
        logger.info(
            "rag_answer_completed",
            request_id=str(request_id),
            used_chunks=len(context.included_chunk_ids),
            generation_duration_seconds=generation_duration,
            insufficient_context=False,
            grounded=grounded,
        )
        return RAGResponse(
            answer=validation.answer,
            grounded=grounded,
            insufficient_context=False,
            citations=validation.citations,
            retrieved_evidence_count=len(retrieval.evidence),
            used_evidence_count=len(context.included_chunk_ids),
            warnings=list(dict.fromkeys(warnings)),
            query=retrieval.query,
            rewritten_query=retrieval.rewritten_query,
            filters_applied=retrieval.filters_applied,
            request_id=request_id,
            debug=debug,
        )
