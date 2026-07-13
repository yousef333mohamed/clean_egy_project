"""Seed immutable v1 project templates and activate them when no DB prompt is active."""

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.prompt_version import PromptStatus, PromptVersion
from app.prompts.registry import FILE_VERSION, PromptRegistry, TEMPLATE_DIR
from app.prompts.versioning import PROMPT_KEYS


async def seed() -> int:
    created = 0
    async with AsyncSessionLocal() as session:
        registry = PromptRegistry(session)
        for key in sorted(PROMPT_KEYS):
            path = TEMPLATE_DIR / f"{key}.v1.txt"
            if not path.is_file():
                continue
            exists = (await session.execute(select(PromptVersion).where(PromptVersion.prompt_key == key, PromptVersion.version == FILE_VERSION))).scalar_one_or_none()
            if exists is None:
                await registry.create_version(key, FILE_VERSION, path.read_text(encoding="utf-8"), description="Seeded project prompt", created_by="seed_prompt_versions")
                created += 1
            active = (await session.execute(select(PromptVersion).where(PromptVersion.prompt_key == key, PromptVersion.status == PromptStatus.ACTIVE))).scalar_one_or_none()
            if active is None:
                await registry.activate_version(key, FILE_VERSION)
        await session.commit()
    return created


if __name__ == "__main__":
    count = asyncio.run(seed())
    print(f"Seeded {count} prompt versions.")
