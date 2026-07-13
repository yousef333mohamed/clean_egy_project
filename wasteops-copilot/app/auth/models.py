"""Minimal authenticated principal."""

from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUser(BaseModel):
    """Verified identity and effective backend permissions."""

    subject: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    display_name: str | None = Field(default=None, max_length=255)
    roles: set[str] = Field(default_factory=set)
    permissions: set[str] = Field(default_factory=set)
    issuer: str
    token_id: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(frozen=True)
