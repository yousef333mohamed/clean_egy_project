"""OpenAI-compatible chat adapter output and retry tests."""

from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services.llm_service import LLMError, LLMService


def settings():
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        llm_max_retries=1,
    )


class Completions:
    def __init__(self, *, fail_once=False, content="Grounded [S1]"):
        self.fail_once = fail_once
        self.content = content
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_once:
            self.fail_once = False
            raise TimeoutError("temporary")
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))])


@pytest.mark.asyncio
async def test_plain_output_and_retry_without_logging_content() -> None:
    completions = Completions(fail_once=True)
    delays = []

    async def sleep(delay):
        delays.append(delay)

    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    service = LLMService(settings(), client=client, sleep=sleep)
    answer = await service.generate_grounded_answer(system_prompt="system", user_prompt="evidence")
    assert answer == "Grounded [S1]"
    assert len(completions.calls) == 2
    assert delays == [1]


@pytest.mark.asyncio
async def test_empty_prompts_are_rejected() -> None:
    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    with pytest.raises(LLMError):
        await LLMService(settings(), client=client).generate_grounded_answer(system_prompt="", user_prompt="x")
