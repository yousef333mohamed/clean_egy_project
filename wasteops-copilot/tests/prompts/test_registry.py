"""Project fallback prompt resolution and activation validation helpers."""

import pytest

from app.prompts.registry import PromptRegistry
from app.prompts.versioning import content_hash, validate_prompt_content


async def test_versioned_file_fallback_has_hash():
    prompt = await PromptRegistry().get_active_prompt("rag_answer")
    assert prompt.version == "1.0.0" and prompt.content_hash == content_hash(prompt.content) and prompt.source == "project_file"


@pytest.mark.parametrize("content", ["", "  ", "API_KEY=sk-supersecret123456789"])
def test_invalid_prompt_content_is_rejected(content):
    with pytest.raises(ValueError):
        validate_prompt_content(content)
