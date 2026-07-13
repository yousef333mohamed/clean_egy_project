"""Service dependency composition."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.intent_router import IntentRouter
from app.retrieval.sql_retriever import SQLRetriever
from app.retrieval.vector_retriever import VectorRetriever
from app.services.decision_service import DecisionService
from app.services.incident_service import IncidentService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_llm(settings: SettingsDep) -> LLMService:
    return LLMService(settings)


def get_hybrid(session: SessionDep, settings: SettingsDep, llm: Annotated[LLMService, Depends(get_llm)]) -> HybridRetriever:
    return HybridRetriever(IntentRouter(llm), SQLRetriever(session, llm, settings), VectorRetriever(session, settings))


def get_rag(retriever: Annotated[HybridRetriever, Depends(get_hybrid)], llm: Annotated[LLMService, Depends(get_llm)]) -> RAGService:
    return RAGService(retriever, llm)


def get_decision(retriever: Annotated[HybridRetriever, Depends(get_hybrid)], llm: Annotated[LLMService, Depends(get_llm)]) -> DecisionService:
    return DecisionService(retriever, llm)


def get_incident(retriever: Annotated[HybridRetriever, Depends(get_hybrid)], llm: Annotated[LLMService, Depends(get_llm)]) -> IncidentService:
    return IncidentService(retriever, llm)
