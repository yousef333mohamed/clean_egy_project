"""General grounded chat service."""

from app.retrieval.citation_builder import evidence_context
from app.retrieval.hybrid_retriever import HybridRetriever
from app.schemas.chat import ChatResponse
from app.services.llm_service import LLMService


class RAGService:
    """Answer questions using routed evidence."""

    def __init__(self, retriever: HybridRetriever, llm: LLMService) -> None:
        self.retriever = retriever
        self.llm = llm

    async def answer(self, question: str) -> ChatResponse:
        route, evidence = await self.retriever.retrieve(question)
        if route.requires_sql or route.requires_vector_search:
            answer = (
                await self.llm.complete(self.llm.prompt("rag_answer_prompt.txt"), f"Question: {question}\nEvidence:\n{evidence_context(evidence)}")
                if evidence
                else "I do not have enough retrieved evidence to answer that question."
            )
        else:
            answer = (
                await self.llm.complete(self.llm.prompt("system_prompt.txt"), question)
                if self.llm.settings.llm_api_key
                else "WasteOps is ready. Ask about bins, trucks, workforce, incidents, or procedures."
            )
        return ChatResponse(answer=answer, intent=route.intent, evidence=evidence)
