"""Reusable authoritative authentication and permission dependencies."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.development_auth import development_user
from app.auth.jwt_validator import validate_access_token
from app.auth.models import AuthenticatedUser
from app.core.config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)


async def optional_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser | None:
    """Resolve a verified principal without forcing authentication."""
    if not settings.auth_enabled:
        return development_user(settings)
    if credentials is None:
        if settings.allow_development_auth and request.headers.get("X-Development-Auth") == "enabled":
            return development_user(settings)
        return None
    if credentials.scheme.casefold() != "bearer":
        return None
    user = validate_access_token(credentials.credentials, settings)
    request.state.authenticated_user = user
    return user


async def current_user(user: Annotated[AuthenticatedUser | None, Depends(optional_current_user)]) -> AuthenticatedUser:
    """Require an authenticated identity."""
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    return user


CurrentUser = Annotated[AuthenticatedUser, Depends(current_user)]
OptionalCurrentUser = Annotated[AuthenticatedUser | None, Depends(optional_current_user)]


def require_permission(permission: str) -> Callable[..., Awaitable[AuthenticatedUser]]:
    """Build a dependency with inspectable endpoint security metadata."""

    async def dependency(user: CurrentUser) -> AuthenticatedUser:
        if permission not in user.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        return user

    dependency.required_permissions = frozenset({permission})  # type: ignore[attr-defined]
    return dependency


def require_any_permission(*permissions: str) -> Callable[..., Awaitable[AuthenticatedUser]]:
    async def dependency(user: CurrentUser) -> AuthenticatedUser:
        if not user.permissions.intersection(permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        return user

    dependency.required_permissions = frozenset(permissions)  # type: ignore[attr-defined]
    return dependency


def require_role(role: str) -> Callable[..., Awaitable[AuthenticatedUser]]:
    async def dependency(user: CurrentUser) -> AuthenticatedUser:
        if role not in user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    dependency.required_roles = frozenset({role})  # type: ignore[attr-defined]
    return dependency
