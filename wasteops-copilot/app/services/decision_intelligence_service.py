"""Human-approved evidence-to-options Decision Intelligence orchestration."""

import json
import re
import time
import uuid

from app.core.logging import get_logger
from app.decision.enums import ConfidenceLevel, DecisionEvidenceType
from app.schemas.confidence import ConfidenceComponents, DecisionConfidence
from app.schemas.decision import DecisionDebugResponse, DecisionResponse
from app.prompts.registry import PromptRegistry
from app.utils.prompt_loader import load_prompt

logger = get_logger(__name__)
CITATION = re.compile(r"\[([DSRM]\d+)\]")
NUMBER = re.compile(r"(?<![\w-])-?\d+(?:\.\d+)?")
HUMAN_WARNING = "This recommendation is decision support only and must be reviewed by an authorized operations manager before execution."


class DecisionIntelligenceService:
    def __init__(
        self,
        router,
        planner,
        collector,
        option_generator,
        option_scorer,
        confidence_calculator,
        risk_analyzer,
        decision_registry,
        settings,
        *,
        llm_service=None,
    ) -> None:
        self.router = router
        self.planner = planner
        self.collector = collector
        self.option_generator = option_generator
        self.option_scorer = option_scorer
        self.confidence_calculator = confidence_calculator
        self.risk_analyzer = risk_analyzer
        self.decision_registry = decision_registry
        self.settings = settings
        self.llm_service = llm_service
        self.prompt_registry = getattr(llm_service, "prompt_registry", PromptRegistry())

    async def preview(self, request):
        from app.schemas.decision import DecisionPreviewResponse

        route = await self.router.route(request)
        return DecisionPreviewResponse(route=route, plan=self.planner.plan(request, route))

    async def recommend(self, request) -> DecisionResponse:
        response, _debug = await self._run(request)
        return response

    async def debug(self, request) -> DecisionDebugResponse:
        _response, debug = await self._run(request)
        return debug

    async def _run(self, request):
        started = time.perf_counter()
        request_id = uuid.uuid4()
        route = await self.router.route(request)
        plan = self.planner.plan(request, route)
        if route.unsupported_reason or route.requires_data_science or route.requires_optimization:
            response = self._unsupported(request_id, route, plan)
            return response, self._debug(request_id, route, [], [], response.confidence, True)
        collected = await self.collector.collect(request, plan)
        options = self.option_generator.generate(request, route.decision_type, collected.evidence)
        scored = self.option_scorer.score(options, collected.evidence, request.constraints)
        scored = [
            item.model_copy(update={"risks": self.risk_analyzer.analyze(item, collected.evidence), "trade_offs": self._trade_offs(item)}) for item in scored
        ]
        confidence = self.confidence_calculator.calculate(
            collected.evidence,
            plan.required_evidence_categories,
            explicitly_historical=bool(request.scope.start_date or request.scope.end_date),
        )
        useful_db = any(item.source_type == DecisionEvidenceType.DATABASE and item.supporting_values.get("has_data") for item in collected.evidence)
        document_found = bool(collected.document_citations)
        missing = list(plan.missing_requirements)
        if not useful_db:
            missing.append("Matching operational records for the requested scope")
        if not document_found:
            missing.append("Current authoritative procedural guidance")
        elif any(item.source_type == DecisionEvidenceType.DOCUMENT and item.is_synthetic for item in collected.evidence):
            missing.append("A current official procedure to replace synthetic demo guidance")
        missing.append("Confirmed operational resource availability before execution")
        insufficient = (
            len(collected.evidence) < self.settings.decision_min_evidence_items
            or not useful_db
            or bool(plan.missing_requirements)
            or (self.settings.decision_require_document_guidance and not document_found)
            or confidence.score < self.settings.decision_min_confidence
        )
        warnings = list(collected.warnings)
        periods = {(item.data_period.start, item.data_period.end) for item in collected.database_evidence}
        if len(periods) > 1:
            warnings.append("Different evidence sources use different date ranges; each source period remains labeled.")
        dated = [(item.tool_name, item.data_period.end) for item in collected.database_evidence if item.data_period.end]
        if dated:
            newest = max(end for _tool, end in dated)
            if any(tool.startswith("list_") and "bin" in tool and end < newest for tool, end in dated):
                warnings.append("The latest available bin reading is older than other collected operational evidence.")
        warnings.append(HUMAN_WARNING)
        recommended = None if insufficient or not scored else scored[0]
        alternatives = [] if recommended is None else scored[1:]
        if recommended:
            situation = await self._explain(request, recommended, alternatives, confidence, collected, missing, warnings)
        else:
            situation = load_prompt("insufficient_decision_context.txt")
            warnings.append("Confidence or required evidence did not meet the configured recommendation threshold.")
        response = DecisionResponse(
            request_id=request_id,
            decision_type=route.decision_type,
            situation_summary=situation,
            recommended_option=recommended,
            alternative_options=alternatives,
            database_evidence=collected.database_evidence,
            document_citations=collected.document_citations,
            confidence=confidence,
            missing_information=list(dict.fromkeys(missing)),
            warnings=list(dict.fromkeys(warnings)),
            requires_human_approval=True,
            grounded=bool(recommended),
            insufficient_context=insufficient,
        )
        logger.info(
            "decision_completed",
            request_id=str(request_id),
            decision_type=route.decision_type,
            planned_tools=[call.tool for call in plan.analytics_calls],
            database_evidence_count=len(collected.database_evidence),
            document_evidence_count=len(collected.document_citations),
            option_count=len(scored),
            selected_option_id=recommended.option_id if recommended else None,
            score_breakdown=recommended.score_breakdown.model_dump() if recommended else None,
            confidence_components=confidence.components.model_dump(),
            insufficient_context=insufficient,
            processing_duration_seconds=time.perf_counter() - started,
        )
        return response, self._debug(request_id, route, collected.evidence, scored, confidence, insufficient)

    async def _explain(self, request, recommended, alternatives, confidence, collected, missing, warnings) -> str:
        result = {
            "recommended_option": recommended.model_dump(mode="json"),
            "alternatives": [item.model_dump(mode="json") for item in alternatives],
            "confidence": confidence.model_dump(mode="json"),
            "missing_information": missing,
            "requires_human_approval": True,
        }
        if self.llm_service is None:
            warnings.append("Model explanation was unavailable; deterministic decision fields remain authoritative.")
            return self._deterministic_explanation(request.question, recommended, confidence, missing)
        resolved = await self.prompt_registry.get_active_prompt("decision_explanation")
        prompt = resolved.content.format(
            question=request.question,
            result=json.dumps(result, ensure_ascii=False),
            evidence=json.dumps([item.model_dump(mode="json") for item in collected.evidence], ensure_ascii=False),
        )
        answer = await self.llm_service.generate_grounded_answer(
            system_prompt="Explain the fixed deterministic result only. Do not create actions or scores.", user_prompt=prompt,
            prompt_key=resolved.prompt_key, prompt_version=resolved.version,
        )
        valid_ids = {item.evidence_id for item in collected.evidence}
        invalid = set(CITATION.findall(answer)) - valid_ids
        for identifier in invalid:
            answer = answer.replace(f"[{identifier}]", "")
        if invalid:
            warnings.append("Invalid generated decision citations were removed.")
        cited = set(CITATION.findall(answer)) & valid_ids
        if not cited or (recommended.title not in answer and recommended.action not in answer):
            warnings.append("The generated explanation did not preserve the selected option or grounded citations and was replaced.")
            return self._deterministic_explanation(request.question, recommended, confidence, missing)
        serialized = json.dumps(result, ensure_ascii=False) + json.dumps([item.model_dump(mode="json") for item in collected.evidence], ensure_ascii=False)
        plain_answer = CITATION.sub("", answer)
        if re.search(
            r"\b(dispatch|assign workers?|update schedules?|mark maintenance complete|delete records?|execute automatically)\b",
            plain_answer,
            re.IGNORECASE,
        ):
            warnings.append("Generated execution language was replaced with the deterministic decision-support explanation.")
            return self._deterministic_explanation(request.question, recommended, confidence, missing)
        if any(number not in serialized and number not in request.question for number in NUMBER.findall(plain_answer)):
            warnings.append("Generated unsupported numeric claims were replaced with the deterministic explanation.")
            return self._deterministic_explanation(request.question, recommended, confidence, missing)
        return answer

    @staticmethod
    def _deterministic_explanation(question, recommended, confidence, missing) -> str:
        evidence = " ".join(f"[{item}]" for item in recommended.supporting_evidence_ids[:4])
        if re.search(r"[\u0600-\u06ff]", question):
            return (
                f"الإجراء الموصى به: {recommended.title}. {recommended.action} {evidence}\n\n"
                f"حصل هذا الخيار على الدرجة المحددة برمجياً {recommended.score}، ومستوى جودة الأدلة {confidence.score} ({confidence.level}). "
                f"المعلومات الناقصة: {', '.join(missing) if missing else 'لا توجد معلومات ناقصة محددة'}. يلزم اعتماد مدير مخول قبل التنفيذ."
            )
        return (
            f"Recommended action: {recommended.title}. {recommended.action} {evidence}\n\n"
            f"This option ranked first with the deterministic score {recommended.score}; confidence is {confidence.score} ({confidence.level}). "
            f"Missing information: {', '.join(missing) if missing else 'none identified'}. Human approval is required before execution."
        )

    @staticmethod
    def _trade_offs(option) -> list[str]:
        if option.action_category.value == "CONTINUE_MONITORING":
            return ["Monitoring uses fewer immediate resources but may delay resolution of a supported condition."]
        return ["Review may protect service continuity but requires manager-confirmed operational capacity."]

    @staticmethod
    def _unsupported(request_id, route, plan) -> DecisionResponse:
        confidence = DecisionConfidence(
            score=0,
            level=ConfidenceLevel.LOW,
            components=ConfidenceComponents(retrieval_coverage=0, source_quality=0, data_completeness=0, source_agreement=0, recency=0),
            explanation="No confidence score is available because the request is unsupported.",
        )
        reason = route.unsupported_reason or "The request is unsupported."
        return DecisionResponse(
            request_id=request_id,
            decision_type=route.decision_type,
            situation_summary=reason,
            recommended_option=None,
            alternative_options=[],
            database_evidence=[],
            document_citations=[],
            confidence=confidence,
            missing_information=[reason],
            warnings=[reason, HUMAN_WARNING],
            requires_human_approval=True,
            grounded=False,
            insufficient_context=True,
        )

    @staticmethod
    def _debug(request_id, route, evidence, scored, confidence, insufficient):
        return DecisionDebugResponse(
            request_id=request_id,
            router_output=route,
            evidence_summary=[
                {
                    "evidence_id": item.evidence_id,
                    "source_type": item.source_type,
                    "category": item.category,
                    "authority_level": item.authority_level,
                    "recency": item.recency,
                    "has_data": item.supporting_values.get("has_data"),
                }
                for item in evidence
            ],
            option_scores=[{"option_id": item.option_id, "score": item.score, "score_breakdown": item.score_breakdown.model_dump()} for item in scored],
            confidence=confidence,
            insufficient_context=insufficient,
        )
