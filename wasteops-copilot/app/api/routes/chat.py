"""Chat endpoint."""

from typing import Annotated
from fastapi import APIRouter, Depends
from app.api.dependencies import get_rag
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, service: Annotated[RAGService, Depends(get_rag)]) -> ChatResponse:
    """Answer an operational question using routed retrieval."""
    return await service.answer(request.question)
