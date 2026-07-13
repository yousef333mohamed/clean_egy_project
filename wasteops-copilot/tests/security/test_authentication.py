"""OIDC cryptographic validation and authorization behavior."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth.dependencies import require_permission
from app.auth.jwt_validator import validate_access_token
from app.auth.models import AuthenticatedUser
from app.core.config import Settings
from app.core.config import get_settings
from app.main import app

PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = PRIVATE_KEY.public_key()


def settings(**changes) -> Settings:
    values = {
        "database_url": "postgresql+asyncpg://test:test@localhost/test",
        "database_sync_url": "postgresql+psycopg://test:test@localhost/test",
        "auth_enabled": True,
        "oidc_issuer_url": "https://id.example.test",
        "oidc_jwks_url": "https://id.example.test/jwks",
        "oidc_audience": "wasteops-api",
        "rate_limit_enabled": True,
        "redis_required": True,
    }
    values.update(changes)
    return Settings(**values)


def token(**changes) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": "user-1",
        "iss": "https://id.example.test",
        "aud": "wasteops-api",
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
        "roles": ["VIEWER"],
    }
    claims.update(changes)
    return jwt.encode(claims, PRIVATE_KEY, algorithm="RS256", headers={"kid": "test-key"})


@pytest.fixture(autouse=True)
def signing_key(monkeypatch):
    monkeypatch.setattr("app.auth.jwt_validator.CachedJWKSClient.signing_key", lambda self, value: PUBLIC_KEY)


def test_valid_token_maps_role_permissions() -> None:
    user = validate_access_token(token(), settings())
    assert user.subject == "user-1"
    assert "dashboard:read" in user.permissions


@pytest.mark.parametrize(
    "claims",
    [
        {"exp": datetime.now(UTC) - timedelta(minutes=5)},
        {"iss": "https://attacker.example"},
        {"aud": "wrong-api"},
        {"sub": ""},
        {"roles": {"bad": "shape"}},
    ],
)
def test_invalid_claims_return_401(claims) -> None:
    with pytest.raises(HTTPException) as error:
        validate_access_token(token(**claims), settings(jwt_clock_skew_seconds=0))
    assert error.value.status_code == 401


def test_invalid_signature_returns_401(monkeypatch) -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    monkeypatch.setattr("app.auth.jwt_validator.CachedJWKSClient.signing_key", lambda self, value: other_key)
    with pytest.raises(HTTPException) as error:
        validate_access_token(token(), settings())
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_missing_permission_returns_403() -> None:
    dependency = require_permission("audit:read")
    user = AuthenticatedUser(subject="viewer", issuer="test", roles={"VIEWER"}, permissions={"dashboard:read"})
    with pytest.raises(HTTPException) as error:
        await dependency(user)
    assert error.value.status_code == 403


def test_development_auth_cannot_start_in_production() -> None:
    with pytest.raises(ValueError, match="Development authentication"):
        settings(
            app_environment="production",
            allow_development_auth=True,
            cors_allowed_origins="https://app.example.test",
            trusted_hosts="app.example.test",
            enable_retrieval_debug_api=False,
            analytics_enable_debug_api=False,
            enable_decision_debug_api=False,
        )


def test_api_distinguishes_401_and_403(monkeypatch) -> None:
    configured = settings()
    app.dependency_overrides[get_settings] = lambda: configured
    try:
        client = TestClient(app)
        assert client.get("/api/auth/me").status_code == 401
        viewer = AuthenticatedUser(subject="viewer", issuer="test", roles={"VIEWER"}, permissions={"dashboard:read"})
        monkeypatch.setattr("app.auth.dependencies.validate_access_token", lambda *_args: viewer)
        assert client.get("/api/feedback/summary", headers={"Authorization": "Bearer generated-test-token"}).status_code == 403
    finally:
        app.dependency_overrides.clear()
