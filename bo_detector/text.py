from __future__ import annotations

import re
import unicodedata


def normalize_text(value: str | None) -> str:
    """Normalize text for accent-insensitive matching."""
    if not value:
        return ""

    value = value.lower().strip()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def contains_phrase(text: str, phrase: str) -> bool:
    """Return true when phrase appears as a complete normalized phrase."""
    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)
    if not normalized_text or not normalized_phrase:
        return False

    pattern = rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)"
    return re.search(pattern, normalized_text) is not None
