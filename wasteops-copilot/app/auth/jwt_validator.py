"""Cryptographic OIDC access-token validation."""

from typing import Any

import jwt
from fastapi import HTTPException, status

from app.auth.claims import string_set_claim
from app.auth.jwks_client import CachedJWKSClient
from app.auth.models import AuthenticatedUser
from app.auth.permissions import permissions_for_roles
from app.core.config import Settings


def validate_access_token(token: str, settings: Settings) -> AuthenticatedUser:
    """Validate signature and registered claims, then build a minimal principal."""
    try:
        algorithms = [item.strip() for item in settings.jwt_allowed_algorithms.split(",") if item.strip()]
        payload: dict[str, Any] = jwt.decode(
            token,
            CachedJWKSClient(settings).signing_key(token),
            algorithms=algorithms,
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer_url,
            leeway=settings.jwt_clock_skew_seconds,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise jwt.InvalidTokenError("missing subject")
        roles = string_set_claim(payload, settings.oidc_role_claim)
        asserted = string_set_claim(payload, settings.oidc_permission_claim)
        permissions = permissions_for_roles(roles) | asserted
        return AuthenticatedUser(
            subject=subject,
            email=payload.get("email") if isinstance(payload.get("email"), str) else None,
            display_name=payload.get("name") if isinstance(payload.get("name"), str) else None,
            roles=roles,
            permissions=permissions,
            issuer=str(payload["iss"]),
            token_id=payload.get("jti") if isinstance(payload.get("jti"), str) else None,
        )
    except HTTPException:
        raise
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
