"""Deterministic token counting and splitting with tiktoken."""

from functools import lru_cache

import tiktoken


class TokenCounter:
    """Model-aware token encoder with a stable fallback encoding."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.encoding = self._encoding(model)

    @staticmethod
    @lru_cache(maxsize=16)
    def _encoding(model: str) -> tiktoken.Encoding:
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")

    def encode(self, text: str) -> list[int]:
        """Encode text to model tokens."""
        return self.encoding.encode(text)

    def decode(self, tokens: list[int]) -> str:
        """Decode tokens back into text."""
        return self.encoding.decode(tokens)

    def count(self, text: str) -> int:
        """Count model tokens."""
        return len(self.encode(text))
