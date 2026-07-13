"""Explicit, production-forbidden local identity."""

from app.auth.models import AuthenticatedUser
from app.auth.permissions import permissions_for_roles
from app.core.config import Settings


def development_user(settings: Settings) -> AuthenticatedUser:
    roles = {item.strip() for item in settings.development_auth_roles.split(",") if item.strip()}
    return AuthenticatedUser(
        subject=settings.development_auth_user_id,
        email=None,
        display_name="Development user",
        roles=roles,
        permissions=permissions_for_roles(roles),
        issuer="wasteops-development",
        token_id=None,
    )
