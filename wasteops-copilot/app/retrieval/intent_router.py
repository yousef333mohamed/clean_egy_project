"""LLM-first intent routing with deterministic fallback."""

import re
from app.schemas.retrieval import Intent, IntentEntities, IntentResult
from app.services.llm_service import LLMService


class IntentRouter:
    """Classify manager questions and identify retrieval requirements."""

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm

    async def route(self, question: str) -> IntentResult:
        """Use the LLM when configured, falling back on auditable rules."""
        if self.llm and self.llm.settings.llm_api_key:
            try:
                return await self.llm.structured(self.llm.prompt("intent_router_prompt.txt"), question, IntentResult)
            except Exception:
                pass
        return self.fallback(question)

    @staticmethod
    def fallback(question: str) -> IntentResult:
        """Route common operational language without an external dependency."""
        q = question.lower()
        entities = IntentEntities(
            bin_id=(m.group(0) if (m := re.search(r"\bBIN-[\w\-]+", question, re.I)) else None),
            truck_id=(m.group(0) if (m := re.search(r"\bTRK-[\w\-]+", question, re.I)) else None),
            worker_id=(m.group(0) if (m := re.search(r"\bWRK-[\w\-]+", question, re.I)) else None),
        )
        if any(x in q for x in ("report", "write-up")):
            intent = Intent.REPORT_GENERATION
        elif any(x in q for x in ("why", "root cause", "missed", "incident", "investigate")):
            intent = Intent.INCIDENT_INVESTIGATION
        elif any(x in q for x in ("best", "recommend", "plan", "priority", "should")):
            intent = Intent.DECISION_RECOMMENDATION
        elif any(x in q for x in ("procedure", "manual", "policy", "sensor fails", "how to")):
            intent = Intent.DOCUMENT_SEARCH
        elif any(x in q for x in ("which", "how many", "total", "average", "unusual", "performance", "bin", "truck", "worker")):
            intent = Intent.SQL_DATA_QUERY
        else:
            intent = Intent.GENERAL_CONVERSATION
        sql = intent in {Intent.SQL_DATA_QUERY, Intent.INCIDENT_INVESTIGATION, Intent.DECISION_RECOMMENDATION, Intent.REPORT_GENERATION}
        vector = intent in {Intent.DOCUMENT_SEARCH, Intent.INCIDENT_INVESTIGATION, Intent.DECISION_RECOMMENDATION, Intent.REPORT_GENERATION}
        return IntentResult(intent=intent, entities=entities, requires_sql=sql, requires_vector_search=vector)
