"""Citation namespace rules for combined evidence."""

import re

DATABASE_CITATION = re.compile(r"\[D\d+\]")
DOCUMENT_CITATION = re.compile(r"\[S\d+\]")


def cited_ids(answer: str, prefix: str) -> set[str]:
    pattern = DATABASE_CITATION if prefix == "D" else DOCUMENT_CITATION
    return {match[1:-1] for match in pattern.findall(answer)}
