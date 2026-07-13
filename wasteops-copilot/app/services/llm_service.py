"""OpenAI-compatible grounded chat service with explicit retry policy."""

import asyncio
import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.utils.prompt_loader import load_prompt

logger = get_logger(__name__)


class LLMError(RuntimeError):
    """Safe provider failure exposed to orchestration layers."""


class LLMConfigurationError(LLMError):
    """Chat credentials or configuration are unavailable."""


class LLMResponseError(LLMError):
    """The provider returned empty or structurally invalid output."""


class LLMService:
    """Return plain text and validated rewrite JSON, never provider objects."""

    def __init__(self, settings: Settings | None = None, *, client: Any | None = None, sleep: Any = asyncio.sleep) -> None:
        self.settings = settings or get_settings()
        if client is None:
            if not self.settings.llm_api_key:
                raise LLMConfigurationError("LLM_API_KEY is required for grounded answers")
            client = AsyncOpenAI(
                api_key=self.settings.llm_api_key,
                base_url=self.settings.llm_base_url,
                timeout=self.settings.llm_timeout_seconds,
                max_retries=0,
            )
        self.client = client
        self.sleep = sleep

    async def _complete(self, *, messages: list[dict[str, str]], temperature: float, max_tokens: int, json_mode: bool = False) -> str:
        last_error: Exception | None = None
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                logger.info(
                    "llm_request",
                    model=self.settings.chat_model_name,
                    message_count=len(messages),
                    json_mode=json_mode,
                    attempt=attempt + 1,
                )
                kwargs: dict[str, Any] = {
                    "model": self.settings.chat_model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_completion_tokens": max_tokens,
                    "timeout": self.settings.llm_timeout_seconds,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                response = await self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content if response.choices else None
                if not content or not content.strip():
                    raise LLMResponseError("Chat provider returned an empty response")
                return content.strip()
            except LLMResponseError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "llm_request_failed",
                    model=self.settings.chat_model_name,
                    attempt=attempt + 1,
                    error_type=type(exc).__name__,
                )
                if attempt >= self.settings.llm_max_retries:
                    break
                await self.sleep(2**attempt)
        raise LLMError(f"Chat request failed after retries: {type(last_error).__name__}") from last_error

    async def generate_grounded_answer(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        """Generate one answer from caller-controlled system and evidence prompts."""
        if not system_prompt.strip() or not user_prompt.strip():
            raise LLMError("System and user prompts must not be empty")
        return await self._complete(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=self.settings.llm_temperature if temperature is None else temperature,
            max_tokens=self.settings.llm_max_output_tokens if max_output_tokens is None else max_output_tokens,
        )

    async def rewrite_query(self, query: str) -> dict[str, Any]:
        """Return the model's constrained retrieval rewrite as parsed JSON."""
        if not query.strip():
            raise LLMError("Query must not be empty")
        prompt = load_prompt("query_rewrite_prompt.txt").format(question=query)
        content = await self._complete(
            messages=[
                {"role": "system", "content": "Return only valid JSON. Do not answer the user's question."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=400,
            json_mode=True,
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMResponseError("Query rewrite was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise LLMResponseError("Query rewrite must be a JSON object")
        return parsed

    async def route_analytics(self, *, question: str, tool_catalog: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a JSON route proposal; orchestration must validate it against the registry."""
        prompt = load_prompt("analytics_router_prompt.txt").format(
            question=question,
            tool_catalog=json.dumps(tool_catalog, ensure_ascii=False, default=str),
        )
        content = await self._complete(
            messages=[{"role": "system", "content": "Return only valid JSON. Never write SQL."}, {"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=700,
            json_mode=True,
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMResponseError("Analytics route was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise LLMResponseError("Analytics route must be a JSON object")
        return parsed

    async def route_decision(self, *, question: str, decision_types: list[str], tool_catalog: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a decision-route proposal for strict registry validation."""
        prompt = load_prompt("decision_router_prompt.txt").format(
            question=question,
            decision_types=json.dumps(decision_types),
            tool_catalog=json.dumps(tool_catalog, ensure_ascii=False, default=str),
        )
        content = await self._complete(
            messages=[{"role": "system", "content": "Return JSON only. Never write SQL or execute actions."}, {"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800,
            json_mode=True,
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMResponseError("Decision route was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise LLMResponseError("Decision route must be a JSON object")
        return parsed
