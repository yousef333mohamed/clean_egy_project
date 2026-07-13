"""OpenAI-compatible chat service."""

import json
from pathlib import Path
from typing import TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel
from app.core.config import Settings
from app.utils.exceptions import ExternalServiceError

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Small provider-independent wrapper around an OpenAI-compatible API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    def prompt(self, filename: str) -> str:
        """Load a version-controlled prompt."""
        return (Path(__file__).parents[1] / "prompts" / filename).read_text(encoding="utf-8")

    async def complete(self, system: str, user: str) -> str:
        """Generate a text completion."""
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.chat_model_name, temperature=0, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}]
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise ExternalServiceError(str(exc)) from exc

    async def structured(self, system: str, user: str, schema: type[T]) -> T:
        """Generate and strictly validate a JSON response."""
        raw = await self.complete(system + "\nReturn only valid JSON matching this schema:\n" + json.dumps(schema.model_json_schema()), user)
        try:
            return schema.model_validate_json(raw)
        except Exception as exc:
            raise ExternalServiceError(f"Invalid structured LLM response: {exc}") from exc
