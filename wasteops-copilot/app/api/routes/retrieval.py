"""Development-only retrieval diagnostics without chat generation."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DatabaseSession
from app.auth.dependencies import require_permission
from app.core.config import Settings, get_settings
from app.retrieval.factory import build_retrieval_service
from app.retrieval.query_processor import QueryProcessingError
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.embedding_service import EmbeddingError

router = APIRouter(prefix="/retrieval", tags=["retrieval"], dependencies=[Depends(require_permission("assistant:use"))])
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.post("/search", response_model=RetrievalResponse)
async def search(request: RetrievalRequest, session: DatabaseSession, settings: AppSettings) -> RetrievalResponse:
    """Retrieve ranked evidence without invoking the chat model."""
    if not settings.enable_retrieval_debug_api:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Retrieval debug API is disabled")
    try:
        response = await build_retrieval_service(session, settings).search(request)
    except QueryProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Embedding provider unavailable") from exc
    allow_content = request.include_content and (settings.app_environment not in {"production", "staging"} or settings.retrieval_allow_production_content)
    if not allow_content:
        response.evidence = [item.model_copy(update={"content": None}) for item in response.evidence]
    if not request.debug:
        response.debug = None
    return response
