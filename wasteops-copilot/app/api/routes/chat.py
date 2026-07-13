"""Grounded RAG chat endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DatabaseSession
from app.core.config import Settings, get_settings
from app.retrieval.factory import build_rag_service
from app.retrieval.query_processor import QueryProcessingError
from app.schemas.chat import RAGRequest, RAGResponse
from app.services.embedding_service import EmbeddingError
from app.services.llm_service import LLMError

router = APIRouter(prefix="/chat", tags=["chat"])
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
