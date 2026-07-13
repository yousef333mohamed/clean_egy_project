"""Deterministic lexical overlap and near-duplicate helpers."""

import re
from collections import Counter


def terms(text: str) -> set[str]:
    return {token.casefold() for token in re.findall(r"[\w\u0600-\u06ff-]+", text) if len(token) > 1}


def term_coverage(query: str, content: str) -> float:
    query_terms = terms(query)
    return len(query_terms & terms(content)) / len(query_terms) if query_terms else 0.0


def identifiers(text: str) -> set[str]:
    return {match.casefold() for match in re.findall(r"\b(?:BIN|TRK|WRK|SOP|POL|CODE)-[\w\u0600-\u06ff-]+", text, re.IGNORECASE)}


def exact_identifier_match(query: str, content: str) -> bool:
    query_ids = identifiers(query)
    return bool(query_ids and query_ids & identifiers(content))


def limit_document_chunks(items: list, maximum: int) -> list:
    counts: Counter[str] = Counter()
    selected = []
    hashes: set[str] = set()
    chunk_ids: set[str] = set()
    for item in items:
        if item.chunk_id in chunk_ids or (item.content_hash and item.content_hash in hashes):
            continue
        if counts[item.document_id] >= maximum:
            continue
        selected.append(item)
        counts[item.document_id] += 1
        chunk_ids.add(item.chunk_id)
        if item.content_hash:
            hashes.add(item.content_hash)
    return selected
