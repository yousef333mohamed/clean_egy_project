"""Prompt administration contracts that never return prompt content."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.prompt_version import PromptStatus


class PromptVersionCreate(BaseModel):
    version: str
    content: str = Field(min_length=1, max_length=100_000)
    description: str | None = Field(default=None, max_length=500)
    created_by: str | None = Field(default=None, max_length=120)


class PromptVersionSummary(BaseModel):
    id: uuid.UUID
    prompt_key: str
    version: str
    content_hash: str
    description: str | None
    status: PromptStatus
    created_by: str | None
    created_at: datetime
    activated_at: datetime | None
    deactivated_at: datetime | None

    model_config = {"from_attributes": True}


class PromptKeySummary(BaseModel):
    prompt_key: str
    active_version: str | None
    source: str
