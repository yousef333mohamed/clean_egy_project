"""Incident contracts."""

from pydantic import BaseModel, Field
from app.schemas.retrieval import Evidence


class IncidentRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


class IncidentResponse(BaseModel):
    summary: str
    timeline: list[str]
    probable_factors: list[str]
    recommended_actions: list[str]
    evidence: list[Evidence]
    missing_information: list[str]
