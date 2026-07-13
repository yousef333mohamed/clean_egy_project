"""Database-first prompt registry with immutable versioned-file fallback."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.models.prompt_version import PromptStatus, PromptVersion
from app.prompts.versioning import content_hash, validate_prompt_content, validate_prompt_key, validate_version

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
FILE_VERSION = "1.0.0"


class PromptNotFoundError(LookupError):
    """No active database prompt or versioned project fallback exists."""


@dataclass(frozen=True)
class ResolvedPrompt:
    prompt_key: str
    version: str
    content: str
    content_hash: str
    source: str


class PromptRegistry:
    """Resolve and transactionally administer allow-listed prompt versions."""

    def __init__(self, session: Any | None = None, *, template_dir: Path = TEMPLATE_DIR) -> None:
        self.session = session
        self.template_dir = template_dir

    async def get_active_prompt(self, prompt_key: str) -> ResolvedPrompt:
        validate_prompt_key(prompt_key)
        if self.session is not None:
            result = await self.session.execute(
                select(PromptVersion).where(PromptVersion.prompt_key == prompt_key, PromptVersion.status == PromptStatus.ACTIVE)
            )
            record = result.scalar_one_or_none()
            if record is not None:
                return ResolvedPrompt(record.prompt_key, record.version, record.content, record.content_hash, "database")
        path = self.template_dir / f"{prompt_key}.v1.txt"
        if not path.is_file():
            raise PromptNotFoundError(f"No active prompt exists for {prompt_key}")
        content = validate_prompt_content(path.read_text(encoding="utf-8"))
        return ResolvedPrompt(prompt_key, FILE_VERSION, content, content_hash(content), "project_file")

    async def create_version(
        self, prompt_key: str, version: str, content: str, *, description: str | None = None, created_by: str | None = None
    ) -> PromptVersion:
        if self.session is None:
            raise RuntimeError("A database session is required to create prompt versions")
        validate_prompt_key(prompt_key)
        validate_version(version)
        content = validate_prompt_content(content)
        existing = await self.session.execute(select(PromptVersion.id).where(PromptVersion.prompt_key == prompt_key, PromptVersion.version == version))
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Prompt version already exists")
        record = PromptVersion(
            prompt_key=prompt_key,
            version=version,
            content=content,
            content_hash=content_hash(content),
            description=description,
            created_by=created_by,
            status=PromptStatus.DRAFT,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def activate_version(self, prompt_key: str, version: str) -> PromptVersion:
        from datetime import UTC, datetime

        if self.session is None:
            raise RuntimeError("A database session is required to activate prompt versions")
        validate_prompt_key(prompt_key)
        result = await self.session.execute(
            select(PromptVersion).where(PromptVersion.prompt_key == prompt_key, PromptVersion.version == version).with_for_update()
        )
        target = result.scalar_one_or_none()
        if target is None:
            raise PromptNotFoundError(f"Prompt version not found: {prompt_key} {version}")
        if target.status == PromptStatus.ARCHIVED:
            raise ValueError("Archived prompts must be explicitly restored before activation")
        validate_prompt_content(target.content)
        now = datetime.now(UTC)
        active_result = await self.session.execute(
            select(PromptVersion).where(PromptVersion.prompt_key == prompt_key, PromptVersion.status == PromptStatus.ACTIVE).with_for_update()
        )
        for active in active_result.scalars():
            if active.id != target.id:
                active.status = PromptStatus.INACTIVE
                active.deactivated_at = now
        target.status = PromptStatus.ACTIVE
        target.activated_at = now
        target.deactivated_at = None
        await self.session.flush()
        return target

    async def archive_version(self, prompt_key: str, version: str) -> PromptVersion:
        if self.session is None:
            raise RuntimeError("A database session is required to archive prompt versions")
        result = await self.session.execute(
            select(PromptVersion).where(PromptVersion.prompt_key == validate_prompt_key(prompt_key), PromptVersion.version == version).with_for_update()
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise PromptNotFoundError("Prompt version not found")
        if record.status == PromptStatus.ACTIVE:
            raise ValueError("Deactivate an active prompt by activating another version before archiving")
        record.status = PromptStatus.ARCHIVED
        await self.session.flush()
        return record

    async def restore_version(self, prompt_key: str, version: str) -> PromptVersion:
        if self.session is None:
            raise RuntimeError("A database session is required to restore prompt versions")
        result = await self.session.execute(
            select(PromptVersion).where(PromptVersion.prompt_key == validate_prompt_key(prompt_key), PromptVersion.version == version)
        )
        record = result.scalar_one_or_none()
        if record is None or record.status != PromptStatus.ARCHIVED:
            raise PromptNotFoundError("Archived prompt version not found")
        record.status = PromptStatus.INACTIVE
        await self.session.flush()
        return record
