from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from .text import normalize_text


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config_keywords.json"


@dataclass(frozen=True)
class KeywordEntry:
    original: str
    normalized: str


@dataclass(frozen=True)
class DetectorConfig:
    poderes_incluidos: tuple[KeywordEntry, ...]
    tipos_norma_incluidos: tuple[KeywordEntry, ...]
    keywords: tuple[KeywordEntry, ...]
    keywords_requieren_accion_normativa: tuple[KeywordEntry, ...]
    verbos_accion: tuple[re.Pattern[str], ...]
    normas_curadas: tuple[re.Pattern[str], ...]
    organismos_prioridad: tuple[KeywordEntry, ...]


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> DetectorConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))

    _require_fields(
        raw,
        {
            "KEYWORDS",
            "PODERES_INCLUIDOS",
            "TIPOS_NORMA_INCLUIDOS",
            "VERBOS_ACCION",
            "LISTA_NORMAS_CURADAS",
            "LISTA_ORGANISMOS_PRIORIDAD",
        },
    )

    return DetectorConfig(
        poderes_incluidos=_keyword_entries(raw["PODERES_INCLUIDOS"]),
        tipos_norma_incluidos=_keyword_entries(raw["TIPOS_NORMA_INCLUIDOS"]),
        keywords=_keyword_entries(raw["KEYWORDS"]),
        keywords_requieren_accion_normativa=_keyword_entries(
            raw.get("KEYWORDS_REQUIEREN_ACCION_NORMATIVA", [])
        ),
        verbos_accion=_compile_patterns(raw["VERBOS_ACCION"]),
        normas_curadas=_compile_patterns(raw["LISTA_NORMAS_CURADAS"]),
        organismos_prioridad=_keyword_entries(raw["LISTA_ORGANISMOS_PRIORIDAD"]),
    )


def _require_fields(raw: dict, fields: set[str]) -> None:
    missing = sorted(fields - set(raw))
    if missing:
        raise ValueError(f"Missing config fields: {', '.join(missing)}")


def _keyword_entries(values: list[str]) -> tuple[KeywordEntry, ...]:
    return tuple(KeywordEntry(original=value, normalized=normalize_text(value)) for value in values)


def _compile_patterns(values: list[str]) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(value, flags=re.IGNORECASE) for value in values)
