"""Chat contracts."""

from pydantic import BaseModel, Field
from app.schemas.retrieval import Evidence, Intent


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    intent: Intent
    evidence: list[Evidence] = Field(default_factory=list)
