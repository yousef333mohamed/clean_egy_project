"""Bounded, cached JWKS lookup."""

import jwt
from functools import lru_cache

from app.core.config import Settings


class CachedJWKSClient:
    """Wrap PyJWT's cache and unknown-kid refresh behavior."""

    def __init__(self, settings: Settings) -> None:
        self._client = _client(settings.oidc_jwks_url, settings.jwks_cache_ttl_seconds, settings.jwks_request_timeout_seconds)

    def signing_key(self, token: str):
        return self._client.get_signing_key_from_jwt(token).key


@lru_cache(maxsize=8)
def _client(url: str, lifespan: int, timeout: float) -> jwt.PyJWKClient:
    """Share bounded JWKS caches between requests and refresh on unknown key IDs."""
    return jwt.PyJWKClient(url, cache_keys=True, cache_jwk_set=True, lifespan=lifespan, timeout=timeout)
