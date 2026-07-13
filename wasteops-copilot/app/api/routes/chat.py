"""Grounded RAG chat endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DatabaseSession
from app.auth.dependencies import require_permission
from app.core.config import Settings, get_settings
from app.retrieval.factory import build_rag_service
from app.analytics.factory import build_hybrid_service
from app.analytics.query_executor import AnalyticsDatabaseError
from app.retrieval.query_processor import QueryProcessingError
from app.schemas.chat import RAGRequest, RAGResponse
from app.schemas.hybrid_answer import HybridQuestionRequest, HybridQuestionResponse
from app.services.embedding_service import EmbeddingError
from app.services.llm_service import LLMError

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_permission("assistant:use"))])
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.post("/rag", response_model=RAGResponse)
async def answer_rag(request: RAGRequest, session: DatabaseSession, settings: AppSettings) -> RAGResponse:
    """Answer only from retrieved evidence or return insufficient context."""
    if not settings.enable_chat_api:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat API is disabled")
    try:
        return await build_rag_service(session, settings).answer(request)
    except QueryProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except (EmbeddingError, LLMError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI provider unavailable") from exc


@router.post("/hybrid", response_model=HybridQuestionResponse)
async def answer_hybrid(request: HybridQuestionRequest, session: DatabaseSession, settings: AppSettings) -> HybridQuestionResponse:
    """Answer through approved structured tools, document RAG, or both."""
    if not settings.enable_hybrid_chat_api:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hybrid chat API is disabled")
    try:
        return await build_hybrid_service(session, settings).answer(request)
    except (EmbeddingError, LLMError, AnalyticsDatabaseError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Hybrid intelligence dependency unavailable") from exc
