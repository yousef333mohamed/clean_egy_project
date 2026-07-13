"""Conservative content cleaning and transparent language detection."""

import re


def clean_text(text: str) -> str:
    """Normalize extraction noise without changing identifiers or meaning."""
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00ad", "")
    lines: list[str] = []
    blank = False
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            if lines and not blank:
                lines.append("")
            blank = True
            continue
        lines.append(line)
        blank = False
    return "\n".join(lines).strip()


def detect_language(text: str) -> str:
    """Classify Arabic/Latin script ratios as ar, en, mixed, or unknown."""
    arabic = len(re.findall(r"[\u0600-\u06ff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    total = arabic + latin
    if total == 0:
        return "unknown"
    if arabic / total >= 0.85:
        return "ar"
    if latin / total >= 0.85:
        return "en"
    return "mixed"
