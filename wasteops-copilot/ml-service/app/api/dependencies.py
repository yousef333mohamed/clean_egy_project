"""Authentication, request IDs, and service composition."""

import hmac
from functools import lru_cache

from fastapi import Header, HTTPException, Request, status

from app.core.config import get_settings
from app.core.database import create_read_only_engine
from app.inference.feature_repository import FeatureRepository
from app.inference.model_loader import ModelLoader
from app.inference.prediction_service import PredictionService
from app.registry.model_registry import ModelRegistry


def _bearer(authorization: str | None) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.casefold() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Service authentication required")
    return token


def require_service_identity(authorization: str | None = Header(default=None)) -> str:
    settings = get_settings()
    token = _bearer(authorization)
    if not settings.service_token or not hmac.compare_digest(token, settings.service_token):
        raise HTTPException(status_code=403, detail="Invalid service identity")
    return "wasteops-backend"


def require_admin_identity(authorization: str | None = Header(default=None)) -> str:
    settings = get_settings()
    token = _bearer(authorization)
    if not settings.admin_service_token or not hmac.compare_digest(token, settings.admin_service_token):
        raise HTTPException(status_code=403, detail="Administrative service identity required")
    return "wasteops-admin"


def request_id(request: Request, x_request_id: str | None = Header(default=None)) -> str:
    return getattr(request.state, "request_id", None) or x_request_id or "unassigned"


@lru_cache
def prediction_service() -> PredictionService:
    settings = get_settings()
    registry = model_registry()
    service = PredictionService(FeatureRepository(create_read_only_engine(settings.analytics_database_url)), settings)
    loader = ModelLoader(registry, {item.strip() for item in settings.allowed_model_checksums.split(",") if item.strip()})
    targets = {
        "bin-overflow": "overflow_model",
        "collection-priority": "priority_model",
        "truck-anomaly": "truck_model",
        "missed-collection": "missed_model",
        "workforce-forecast": "workforce_model",
    }
    active = registry.active()
    for metadata in active:
        setattr(service, targets[metadata.model_name], loader.load(metadata))
    if settings.require_production_models and set(targets) - {item.model_name for item in active}:
        raise RuntimeError("Required production models are unavailable")
    return service


@lru_cache
def model_registry() -> ModelRegistry:
    return ModelRegistry(get_settings().model_artifact_directory)
