"""Token-budgeted, injection-resistant evidence context construction."""

from app.retrieval.citation_builder import CitationBuilder
from app.schemas.retrieval import BuiltContext, RetrievedEvidence
from app.utils.token_counter import TokenCounter

SUSPICIOUS_PATTERNS = (
    "ignore previous instructions",
    "reveal the system prompt",
    "print api keys",
    "execute this command",
)


def sanitize_untrusted_content(content: str) -> tuple[str, bool]:
    """Remove obvious instruction lines while retaining the source for review."""
    suspicious = False
    safe_lines = []
    for line in content.splitlines():
        if any(pattern in line.casefold() for pattern in SUSPICIOUS_PATTERNS):
            suspicious = True
            safe_lines.append("[Suspicious instruction-like text omitted from RAG context]")
        else:
            safe_lines.append(line)
    return "\n".join(safe_lines), suspicious


def remove_repeated_overlap(previous: str, current: str, maximum_words: int = 120) -> str:
    """Remove an exact repeated suffix/prefix while preserving whole words."""
    prior_words = previous.split()
    current_words = current.split()
    maximum = min(maximum_words, len(prior_words), len(current_words))
    for size in range(maximum, 4, -1):
        if [word.casefold() for word in prior_words[-size:]] == [word.casefold() for word in current_words[:size]]:
            return " ".join(current_words[size:])
    return current


class ContextBuilder:
    """Build delimited evidence blocks; retrieved text is never instruction text."""

    def __init__(self, counter: TokenCounter, citation_builder: CitationBuilder | None = None) -> None:
        self.counter = counter
        self.citation_builder = citation_builder or CitationBuilder()

    def _block(self, item: RetrievedEvidence, citation_id: str, content: str) -> str:
        return (
            f"[SOURCE {citation_id}]\n"
            f"Title: {item.document_title}\n"
            f"File: {item.source_filename}\n"
            f"Document type: {item.document_type or 'unknown'}\n"
            f"Section: {item.section_title or 'N/A'}\n"
            f"Page: {item.page_number if item.page_number is not None else 'N/A'}\n"
            f"Authority: {item.authority_level}\n"
            f"Synthetic demo document: {'Yes' if item.is_synthetic else 'No'}\n\n"
            "BEGIN UNTRUSTED EVIDENCE CONTENT\n"
            f"{content}\n"
            "END UNTRUSTED EVIDENCE CONTENT\n"
            f"[END SOURCE {citation_id}]"
        )

    def build(self, evidence: list[RetrievedEvidence], *, max_tokens: int) -> BuiltContext:
        included: list[RetrievedEvidence] = []
        excluded: list[str] = []
        blocks: list[str] = []
        warnings: list[str] = []
        used = 0
        truncated = False
        previous_content = ""
        for item in evidence:
            content, suspicious = sanitize_untrusted_content(item.content or item.content_preview)
            if previous_content:
                content = remove_repeated_overlap(previous_content, content)
            if not content.strip():
                excluded.append(item.chunk_id)
                continue
            citation_id = f"S{len(included) + 1}"
            block = self._block(item, citation_id, content)
            block_tokens = self.counter.count(block)
            if used + block_tokens > max_tokens:
                truncated = True
                if not included:
                    words = content.split()
                    kept: list[str] = []
                    for word in words:
                        candidate_content = " ".join([*kept, word])
                        candidate_block = self._block(item, citation_id, candidate_content)
                        if self.counter.count(candidate_block) > max_tokens:
                            break
                        kept.append(word)
                    if kept:
                        content = " ".join(kept)
                        block = self._block(item, citation_id, content)
                        block_tokens = self.counter.count(block)
                    else:
                        excluded.append(item.chunk_id)
                        continue
                else:
                    excluded.append(item.chunk_id)
                    continue
            if suspicious:
                warnings.append(f"Potential prompt-injection text was omitted from chunk {item.chunk_id}.")
            included.append(item)
            blocks.append(block)
            used += block_tokens
            previous_content = content
        citations = self.citation_builder.assign(included)
        return BuiltContext(
            context_text="\n\n".join(blocks),
            citations=citations,
            included_chunk_ids=[item.chunk_id for item in included],
            excluded_chunk_ids=excluded,
            estimated_tokens=used,
            truncated=truncated,
            warnings=warnings,
        )
