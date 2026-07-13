import pytest
from fastapi import HTTPException

from app.api import dependencies
from app.core.config import Settings


def test_prediction_authentication_rejects_missing_and_wrong_token(monkeypatch):
    monkeypatch.setattr(dependencies, "get_settings", lambda: Settings(service_token="correct", admin_service_token="admin"))
    with pytest.raises(HTTPException):
        dependencies.require_service_identity(None)
    with pytest.raises(HTTPException):
        dependencies.require_service_identity("Bearer wrong")
    assert dependencies.require_service_identity("Bearer correct") == "wasteops-backend"


def test_admin_token_is_separate(monkeypatch):
    monkeypatch.setattr(dependencies, "get_settings", lambda: Settings(service_token="service", admin_service_token="admin"))
    with pytest.raises(HTTPException):
        dependencies.require_admin_identity("Bearer service")
    assert dependencies.require_admin_identity("Bearer admin") == "wasteops-admin"
