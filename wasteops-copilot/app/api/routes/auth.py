"""Safe current-identity endpoints."""

from fastapi import APIRouter

from app.auth.dependencies import CurrentUser
from app.auth.schemas import CurrentUserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me", response_model=CurrentUserResponse)
async def me(user: CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(
        subject=user.subject, email=user.email, display_name=user.display_name, roles=sorted(user.roles), permissions=sorted(user.permissions)
    )


@router.get("/permissions", response_model=list[str])
async def permissions(user: CurrentUser) -> list[str]:
    return sorted(user.permissions)
