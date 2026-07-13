"""Grounded natural-language explanations of structured operational evidence."""

import json
import re
import time
import uuid

from app.schemas.analytics import AnalyticsResponse, DatabaseCitation
from app.prompts.registry import PromptRegistry
from app.services.llm_service import LLMConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)

D_CITATION = re.compile(r"\[D(\d+)\]")
NUMBER = re.compile(r"(?<![\w-])-?\d+(?:\.\d+)?")


class AnalyticsAnswerService:
    def __init__(self, llm_service) -> None:
        self.llm_service = llm_service
        self.prompt_registry = getattr(llm_service, "prompt_registry", PromptRegistry())

    @staticmethod
    def _insufficient(evidence) -> bool:
        if not evidence.rows:
            return True
        row = evidence.rows[0]
        count_keys = [key for key in row if key in {"records_included", "trip_count", "attendance_record_count", "region_day_records_included"}]
        return bool(count_keys) and all(row[key] == 0 for key in count_keys)

    async def answer(self, *, question: str, decision, evidence, request_id: uuid.UUID | None = None) -> AnalyticsResponse:
        request_id = request_id or uuid.uuid4()
        insufficient = self._insufficient(evidence)
        warnings = list(evidence.notes)
        if insufficient:
            warnings.insert(0, "No matching operational records were found.")
            answer = "No matching operational records were found for the requested filters and period. [D1]"
        else:
            if self.llm_service is None:
                raise LLMConfigurationError("LLM_API_KEY is required for generated analytics answers")
            resolved = await self.prompt_registry.get_active_prompt("analytics_answer")
            prompt = resolved.content.format(
                question=question, evidence=json.dumps(evidence.model_dump(mode="json"), ensure_ascii=False)
            )
            generation_started = time.perf_counter()
            answer = await self.llm_service.generate_grounded_answer(
                system_prompt="Use only D-prefixed structured evidence. Never expose or generate SQL.", user_prompt=prompt,
                prompt_key=resolved.prompt_key, prompt_version=resolved.version,
            )
            logger.info(
                "analytics_answer_generated",
                request_id=str(request_id),
                tool_name=evidence.tool_name,
                generation_duration_seconds=time.perf_counter() - generation_started,
            )
            evidence_text = json.dumps(evidence.model_dump(mode="json"), ensure_ascii=False)
            answer_without_citations = D_CITATION.sub("", answer)
            unexpected_numbers = {number for number in NUMBER.findall(answer_without_citations) if number not in evidence_text and number not in question}
            if unexpected_numbers:
                answer = f"Structured result for the requested period: {json.dumps(evidence.rows, ensure_ascii=False)} [D1]"
                warnings.append("Generated unsupported numeric claims were replaced with exact database evidence.")
        valid = {evidence.evidence_id}
        referenced = {f"D{number}" for number in D_CITATION.findall(answer)}
        invalid = referenced - valid
        for citation in invalid:
            answer = answer.replace(f"[{citation}]", "")
        if invalid:
            warnings.append("Invalid generated database citations were removed.")
        referenced &= valid
        citations = [DatabaseCitation(citation_id=item, tool_name=evidence.tool_name, description=evidence.description) for item in sorted(referenced)]
        return AnalyticsResponse(
            answer=answer.strip(),
            route=decision.route,
            tool_name=decision.tool_name,
            domain=decision.domain,
            grounded=bool(citations),
            insufficient_data=insufficient,
            database_evidence=[evidence],
            citations=citations,
            warnings=list(dict.fromkeys(warnings)),
            request_id=request_id,
        )
