"""Feature-gated prompt administration; protect with authentication before production."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import DatabaseSession
from app.auth.dependencies import require_permission
from app.auth.dependencies import CurrentUser
from app.core.config import Settings, get_settings
from app.models.prompt_version import PromptVersion
from app.prompts.registry import PromptNotFoundError, PromptRegistry
from app.prompts.versioning import PROMPT_KEYS
from app.schemas.prompt_version import PromptKeySummary, PromptVersionCreate, PromptVersionSummary

router = APIRouter(prefix="/prompts", tags=["prompt administration"], dependencies=[Depends(require_permission("prompts:read"))])
AppSettings = Annotated[Settings, Depends(get_settings)]


def _enabled(settings: Settings) -> None:
    if not settings.enable_prompt_admin_api:
        raise HTTPException(status_code=403, detail="Prompt administration API is disabled")


@router.get("", response_model=list[PromptKeySummary])
async def list_prompts(session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    registry = PromptRegistry(session)
    output = []
    for key in sorted(PROMPT_KEYS):
        try:
            prompt = await registry.get_active_prompt(key)
            output.append(PromptKeySummary(prompt_key=key, active_version=prompt.version, source=prompt.source))
        except PromptNotFoundError:
            output.append(PromptKeySummary(prompt_key=key, active_version=None, source="missing"))
    return output


@router.get("/{prompt_key}/versions", response_model=list[PromptVersionSummary])
async def list_versions(prompt_key: str, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    if prompt_key not in PROMPT_KEYS:
        raise HTTPException(status_code=404, detail="Prompt key not found")
    return list(
        (await session.execute(select(PromptVersion).where(PromptVersion.prompt_key == prompt_key).order_by(PromptVersion.created_at.desc()))).scalars()
    )


@router.post("/{prompt_key}/versions", response_model=PromptVersionSummary, status_code=201, dependencies=[Depends(require_permission("prompts:create"))])
async def create_version(prompt_key: str, request: PromptVersionCreate, session: DatabaseSession, settings: AppSettings, user: CurrentUser):
    _enabled(settings)
    try:
        record = await PromptRegistry(session).create_version(
            prompt_key, request.version, request.content, description=request.description, created_by=user.subject
        )
        await session.commit()
        await session.refresh(record)
        return record
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Prompt version already exists") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{prompt_key}/versions/{version}/activate", response_model=PromptVersionSummary, dependencies=[Depends(require_permission("prompts:activate"))])
async def activate(prompt_key: str, version: str, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    try:
        record = await PromptRegistry(session).activate_version(prompt_key, version)
        await session.commit()
        await session.refresh(record)
        return record
    except PromptNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{prompt_key}/versions/{version}/archive", response_model=PromptVersionSummary, dependencies=[Depends(require_permission("prompts:archive"))])
async def archive(prompt_key: str, version: str, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    try:
        record = await PromptRegistry(session).archive_version(prompt_key, version)
        await session.commit()
        await session.refresh(record)
        return record
    except PromptNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
