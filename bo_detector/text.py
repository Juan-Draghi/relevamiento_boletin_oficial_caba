from __future__ import annotations

from functools import lru_cache
import re
import unicodedata


@lru_cache(maxsize=16384)
def normalize_text(value: str | None) -> str:
    """Normalize text for accent-insensitive matching.

    El resultado se guarda en cache porque el clasificador normaliza el mismo
    sumario una vez por cada keyword.
    """
    if not value:
        return ""

    value = value.lower().strip()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


@lru_cache(maxsize=4096)
def _phrase_pattern(normalized_phrase: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)")


def contains_phrase(text: str, phrase: str) -> bool:
    """Return true when phrase appears as a complete normalized phrase."""
    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)
    if not normalized_text or not normalized_phrase:
        return False

    return _phrase_pattern(normalized_phrase).search(normalized_text) is not None
