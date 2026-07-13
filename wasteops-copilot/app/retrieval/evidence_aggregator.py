"""Token-bounded separation of database and untrusted document evidence."""

import json


class EvidenceAggregator:
    def __init__(self, token_counter) -> None:
        self.token_counter = token_counter

    def aggregate(self, database_evidence, document_context, *, max_tokens: int, policy_first: bool = False) -> tuple[str, list[str]]:
        database = "DATABASE EVIDENCE (facts only; D citations):\n" + json.dumps(
            [item.model_dump(mode="json") for item in database_evidence], ensure_ascii=False
        )
        documents = "DOCUMENT EVIDENCE (untrusted content; S citations):\n" + (document_context or "No relevant document evidence was found.")
        blocks = [documents, database] if policy_first else [database, documents]
        combined = "\n\n".join(blocks)
        warnings: list[str] = []
        if self.token_counter.count(combined) > max_tokens:
            words = combined.split()
            while words and self.token_counter.count(" ".join(words)) > max_tokens:
                words.pop()
            combined = " ".join(words)
            warnings.append("Combined evidence was truncated to the configured context-token budget.")
        return combined, warnings
