"""Transport boundary and object-key security tests."""

import hashlib

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from types import SimpleNamespace

from app.main import app
from app.core.config import Settings
from app.storage.local import LocalObjectStorage
from app.security.rate_limit import RateLimitMiddleware


def test_untrusted_cors_preflight_is_rejected() -> None:
    response = TestClient(app).options("/api/health", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_host_header_is_rejected() -> None:
    response = TestClient(app).get("/api/health/live", headers={"Host": "evil.example"})
    assert response.status_code == 400


def test_oversized_request_is_rejected() -> None:
    response = TestClient(app).post("/api/chat/rag", content=b"x", headers={"Content-Length": str(20_000_000)})
    assert response.status_code == 413


def test_security_headers_are_present() -> None:
    response = TestClient(app).get("/api/health/live")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in response.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_local_storage_rejects_traversal_and_validates_hash(tmp_path) -> None:
    storage = LocalObjectStorage(str(tmp_path))
    with pytest.raises(ValueError):
        await storage.get("../secret")
    data = b"safe"
    key = await storage.put("documents", data, sha256=hashlib.sha256(data).hexdigest())
    assert await storage.get(key) == data
    with pytest.raises(ValueError, match="hash"):
        await storage.put("documents", data, sha256="0" * 64)


def test_rate_limit_returns_429(monkeypatch) -> None:
    limited = FastAPI()
    settings = SimpleNamespace(
        rate_limit_enabled=True,
        redis_url="redis://unused",
        redis_required=False,
        rate_limit_default_per_minute=1,
        rate_limit_expensive_per_minute=1,
        rate_limit_admin_per_minute=1,
        rate_limit_key_prefix="test",
    )
    limited.add_middleware(RateLimitMiddleware, settings=settings)
    monkeypatch.setattr(RateLimitMiddleware, "_count", lambda self, key, window: _increment(self))
    limited.get("/api/value")(lambda: {"ok": True})
    client = TestClient(limited)
    assert client.get("/api/value").status_code == 200
    response = client.get("/api/value")
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"


async def _increment(instance) -> int:
    instance._test_count = getattr(instance, "_test_count", 0) + 1
    return instance._test_count


def test_supported_secrets_can_be_loaded_from_files(tmp_path) -> None:
    values = {
        "database_url": "postgresql+asyncpg://file:file@database/file",
        "database_sync_url": "postgresql+psycopg://file:file@database/file",
    }
    paths = {}
    for name, value in values.items():
        path = tmp_path / name
        path.write_text(value, encoding="utf-8")
        paths[f"{name}_file"] = str(path)
        paths[name] = ""
    loaded = Settings(**paths)
    assert loaded.database_url == values["database_url"]
    assert loaded.database_sync_url == values["database_sync_url"]
