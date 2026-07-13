"""Safe authentication API schemas."""

from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    subject: str
    email: str | None
    display_name: str | None
    roles: list[str]
    permissions: list[str]
