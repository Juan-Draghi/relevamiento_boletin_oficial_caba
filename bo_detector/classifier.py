from __future__ import annotations

from dataclasses import dataclass, field
import re

from .config import DetectorConfig, KeywordEntry
from .text import contains_phrase, normalize_text


RELEVANTE = "RELEVANTE"
REVISION_MANUAL = "REVISION_MANUAL"
NO_RELEVANTE = "NO_RELEVANTE"
DESCARTADA_FILTRO_ESTRUCTURAL = "DESCARTADA_FILTRO_ESTRUCTURAL"

NORM_REFERENCE_RE = re.compile(
    r"\b(ley|decreto|resolucion|disposicion|ordenanza)\s+(?:n(?:ro|°|º)?\.?\s*)?\d",
    flags=re.IGNORECASE,
)
NORMATIVE_CONTEXT_RE = re.compile(
    r"\b(regimen|regulacion|reglamento|reglamentacion|procedimiento|requisitos|criterios|pautas|norma|normas|normativa|codigo|ley|decreto|resolucion|disposicion|ordenanza)\b"
)


@dataclass(frozen=True)
class ClassificationResult:
    categoria_salida: str
    motivo_deteccion: tuple[str, ...] = field(default_factory=tuple)


def classify_norma(norma: dict, config: DetectorConfig) -> ClassificationResult:
    if not passes_structural_filter(norma, config):
        return ClassificationResult(categoria_salida=DESCARTADA_FILTRO_ESTRUCTURAL)

    sumario = str(norma.get("sumario") or "")
    organismo = str(norma.get("organismo") or "")

    keyword_matches = _match_entries(sumario, config.keywords)
    conditional_keywords = {entry.normalized for entry in config.keywords_requieren_accion_normativa}
    direct_keyword_matches = [
        match for match in keyword_matches if match.normalized not in conditional_keywords
    ]
    conditional_keyword_matches = [
        match for match in keyword_matches if match.normalized in conditional_keywords
    ]

    if direct_keyword_matches:
        return ClassificationResult(
            categoria_salida=RELEVANTE,
            motivo_deteccion=tuple(f"keyword_sumario: {match.original}" for match in direct_keyword_matches),
        )

    if conditional_keyword_matches and _has_normative_action_context(sumario, config):
        return ClassificationResult(
            categoria_salida=RELEVANTE,
            motivo_deteccion=tuple(
                f"keyword_condicional_sumario: {match.original}" for match in conditional_keyword_matches
            ),
        )

    curated_matches = _match_patterns(sumario, config.normas_curadas)
    if curated_matches:
        return ClassificationResult(
            categoria_salida=RELEVANTE,
            motivo_deteccion=tuple(f"referencia_norma_curada: {match}" for match in curated_matches),
        )

    motivos: list[str] = []

    organism_matches = _match_entries(organismo, config.organismos_prioridad)
    has_opaque_action = _has_action_verb(sumario, config) and _has_norm_reference(sumario)
    if organism_matches and has_opaque_action:
        motivos.append("sumario_opaco_patron")
        motivos.extend(f"organismo_prioritario: {match.original}" for match in organism_matches)

    if motivos:
        return ClassificationResult(categoria_salida=REVISION_MANUAL, motivo_deteccion=tuple(motivos))

    return ClassificationResult(categoria_salida=NO_RELEVANTE)


def passes_structural_filter(norma: dict, config: DetectorConfig) -> bool:
    poder = str(norma.get("poder") or "")
    tipo_norma = str(norma.get("tipo_norma") or "")
    return _matches_allowed_value(poder, config.poderes_incluidos) and _matches_allowed_value(
        tipo_norma,
        config.tipos_norma_incluidos,
    )


def _matches_allowed_value(text: str, entries: tuple[KeywordEntry, ...]) -> bool:
    normalized = normalize_text(text)
    return any(normalized == entry.normalized for entry in entries)


def _match_entries(text: str, entries: tuple[KeywordEntry, ...]) -> list[KeywordEntry]:
    return [entry for entry in entries if contains_phrase(text, entry.original)]


def _match_patterns(text: str, patterns: tuple[re.Pattern[str], ...]) -> list[str]:
    normalized = normalize_text(text)
    matches: list[str] = []
    for pattern in patterns:
        if pattern.search(text) or pattern.search(normalized):
            matches.append(pattern.pattern)
    return matches


def _has_action_verb(text: str, config: DetectorConfig) -> bool:
    return any(pattern.search(text) for pattern in config.verbos_accion)


def _has_norm_reference(text: str) -> bool:
    return NORM_REFERENCE_RE.search(normalize_text(text)) is not None


def _has_normative_action_context(text: str, config: DetectorConfig) -> bool:
    normalized = normalize_text(text)
    return _has_action_verb(text, config) and NORMATIVE_CONTEXT_RE.search(normalized) is not None
