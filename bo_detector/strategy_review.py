"""Revision de estrategias del detector a partir de los registros guardados.

Este modulo SOLO LEE los JSON semanales y la configuracion. Vuelve a
clasificar en memoria las normas guardadas para:

- informar, termino por termino, como se reparten sus coincidencias entre
  normas relevantes, no relevantes y sin informacion;
- comparar la configuracion vigente con una propuesta de cambios antes de
  aplicarla.

Referencia profesional de cada norma (ver ADR-007 y especificacion):

- RELEVANTE: decision RELEVANTE_CONFIRMADA en alguna copia.
- NO_RELEVANTE: decision NO_RELEVANTE_CONFIRMADA.
- NO_RELEVANTE_LECTURA: sin decision, categoria original oculta
  (NO_RELEVANTE o DESCARTADA_FILTRO_ESTRUCTURAL) y boletin con control
  complementario COMPLETO. Se informa por separado.
- SIN_INFORMACION: cualquier otro caso. No cuenta como relevante ni como
  irrelevante.

"Seleccionada" significa clasificada como RELEVANTE o REVISION_MANUAL, es
decir, presente en la lista principal que se lee.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Any

from .classifier import (
    DESCARTADA_FILTRO_ESTRUCTURAL,
    NO_RELEVANTE,
    RELEVANTE,
    REVISION_MANUAL,
    _has_action_verb,
    _has_norm_reference,
    _has_normative_action_context,
    _match_entries,
    _match_patterns,
    classify_norma,
    passes_structural_filter,
)
from .config import DetectorConfig, config_from_dict
from .review_store import (
    CONTROL_COMPLETO,
    NO_RELEVANTE_CONFIRMADA,
    RELEVANTE_CONFIRMADA,
    SIN_REVISAR,
    load_period_bulletins,
)

REF_RELEVANTE = "RELEVANTE"
REF_NO_RELEVANTE = "NO_RELEVANTE"
REF_NO_RELEVANTE_LECTURA = "NO_RELEVANTE_LECTURA"
REF_SIN_INFORMACION = "SIN_INFORMACION"
REFERENCIAS = (REF_RELEVANTE, REF_NO_RELEVANTE, REF_NO_RELEVANTE_LECTURA, REF_SIN_INFORMACION)

SELECTED_CATEGORIES = {RELEVANTE, REVISION_MANUAL}
HIDDEN_CATEGORIES = {NO_RELEVANTE, DESCARTADA_FILTRO_ESTRUCTURAL}

# Listas que la revision de estrategias puede modificar. El filtro estructural
# (PODERES_INCLUIDOS, TIPOS_NORMA_INCLUIDOS) queda fuera de alcance.
EDITABLE_LISTS = (
    "KEYWORDS",
    "KEYWORDS_REQUIEREN_ACCION_NORMATIVA",
    "VERBOS_ACCION",
    "LISTA_NORMAS_CURADAS",
    "LISTA_ORGANISMOS_PRIORIDAD",
)
OPERATIONS = ("agregar", "eliminar", "reemplazar")
MAX_EXAMPLES = 5


@dataclass
class StoredNorm:
    """Una norma del periodo, contada una sola vez."""

    clave: str
    nombre: str
    poder: str
    tipo_norma: str
    organismo: str
    sumario: str
    url_norma: str
    numero_boletin: str
    fecha_publicacion: str
    categoria_original: str
    referencia: str

    def as_record(self) -> dict[str, str]:
        return {
            "poder": self.poder,
            "tipo_norma": self.tipo_norma,
            "organismo": self.organismo,
            "nombre": self.nombre,
            "sumario": self.sumario,
        }

    def example(self) -> dict[str, str]:
        return {
            "nombre": self.nombre,
            "numero_boletin": self.numero_boletin,
            "fecha_publicacion": self.fecha_publicacion,
            "referencia": self.referencia,
        }


@dataclass
class PeriodData:
    desde: str
    hasta: str
    boletines: int
    normas: list[StoredNorm] = field(default_factory=list)

    def reference_counts(self) -> dict[str, int]:
        counts = {ref: 0 for ref in REFERENCIAS}
        for norm in self.normas:
            counts[norm.referencia] += 1
        return counts


# ---------------------------------------------------------------------------
# Lectura del periodo
# ---------------------------------------------------------------------------


def load_period_norms(data_dir: Path, start: date, end: date) -> PeriodData:
    """Lee las normas del periodo, una vez cada una, con su referencia profesional."""
    if start > end:
        raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")
    bulletins = sorted(
        load_period_bulletins(data_dir, start, end),
        key=lambda item: (str(item[1].get("fecha_publicacion") or ""), item[0]),
    )

    first_copy: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    decisions: dict[str, list[tuple[str, str]]] = {}
    complete_control: dict[str, bool] = {}
    for _key, bulletin in bulletins:
        norms = bulletin.get("normas") if isinstance(bulletin.get("normas"), dict) else {}
        is_complete = bulletin.get("control_complementario") == CONTROL_COMPLETO
        for norm_key, norm in norms.items():
            if not isinstance(norm, dict):
                continue
            first_copy.setdefault(norm_key, (norm, bulletin))
            complete_control[norm_key] = complete_control.get(norm_key, False) or is_complete
            decision = str(norm.get("decision_manual") or SIN_REVISAR)
            if decision != SIN_REVISAR:
                decisions.setdefault(norm_key, []).append((str(norm.get("revisado_en") or ""), decision))

    stored: list[StoredNorm] = []
    for norm_key, (norm, bulletin) in first_copy.items():
        category = str(norm.get("categoria_automatica_original") or "")
        recorded = decisions.get(norm_key)
        latest = max(recorded)[1] if recorded else SIN_REVISAR
        if latest == RELEVANTE_CONFIRMADA:
            reference = REF_RELEVANTE
        elif latest == NO_RELEVANTE_CONFIRMADA:
            reference = REF_NO_RELEVANTE
        elif category in HIDDEN_CATEGORIES and complete_control[norm_key]:
            reference = REF_NO_RELEVANTE_LECTURA
        else:
            reference = REF_SIN_INFORMACION
        stored.append(
            StoredNorm(
                clave=norm_key,
                nombre=str(norm.get("nombre") or norm_key),
                poder=str(norm.get("poder") or ""),
                tipo_norma=str(norm.get("tipo_norma") or ""),
                organismo=str(norm.get("organismo") or ""),
                sumario=str(norm.get("sumario") or ""),
                url_norma=str(norm.get("url_norma") or ""),
                numero_boletin=str(bulletin.get("numero_boletin") or ""),
                fecha_publicacion=str(bulletin.get("fecha_publicacion") or ""),
                categoria_original=category,
                referencia=reference,
            )
        )
    stored.sort(key=lambda item: (item.fecha_publicacion, item.nombre))
    return PeriodData(desde=start.isoformat(), hasta=end.isoformat(), boletines=len(bulletins), normas=stored)


# ---------------------------------------------------------------------------
# Informe por termino
# ---------------------------------------------------------------------------


def _without_entry(config: DetectorConfig, list_name: str, value: str) -> DetectorConfig:
    """Copia de la configuracion sin un valor, para medir si ese valor decide."""
    if list_name == "KEYWORDS":
        return replace(config, keywords=tuple(e for e in config.keywords if e.original != value))
    if list_name == "LISTA_NORMAS_CURADAS":
        return replace(config, normas_curadas=tuple(p for p in config.normas_curadas if p.pattern != value))
    if list_name == "LISTA_ORGANISMOS_PRIORIDAD":
        return replace(
            config,
            organismos_prioridad=tuple(e for e in config.organismos_prioridad if e.original != value),
        )
    raise ValueError(f"Lista no admitida para el informe por termino: {list_name}")


def _term_matches(norm: StoredNorm, list_name: str, entry: Any, config: DetectorConfig, conditional: set[str]) -> bool:
    """True cuando el termino coincide de la forma en que el clasificador lo usa."""
    if list_name == "KEYWORDS":
        if not _match_entries(norm.sumario, (entry,)):
            return False
        if entry.normalized in conditional:
            return _has_normative_action_context(norm.sumario, config)
        return True
    if list_name == "LISTA_NORMAS_CURADAS":
        return bool(_match_patterns(norm.sumario, (entry,)))
    # Organismo prioritario: solo deriva a revision manual con una senal adicional.
    text = " ".join([norm.organismo, norm.nombre, norm.sumario])
    if not _match_entries(text, (entry,)):
        return False
    return _has_action_verb(norm.sumario, config) or _has_norm_reference(norm.sumario)


def term_report(period: PeriodData, config: DetectorConfig) -> list[dict[str, Any]]:
    """Reparto de las coincidencias de cada keyword, norma curada y organismo prioritario."""
    eligible = [norm for norm in period.normas if passes_structural_filter(norm.as_record(), config)]
    conditional = {entry.normalized for entry in config.keywords_requieren_accion_normativa}
    lists: list[tuple[str, tuple[Any, ...]]] = [
        ("KEYWORDS", config.keywords),
        ("LISTA_NORMAS_CURADAS", config.normas_curadas),
        ("LISTA_ORGANISMOS_PRIORIDAD", config.organismos_prioridad),
    ]

    rows: list[dict[str, Any]] = []
    for list_name, entries in lists:
        for entry in entries:
            value = entry.pattern if list_name == "LISTA_NORMAS_CURADAS" else entry.original
            matched = [norm for norm in eligible if _term_matches(norm, list_name, entry, config, conditional)]
            counts = {ref: 0 for ref in REFERENCIAS}
            for norm in matched:
                counts[norm.referencia] += 1

            reduced = _without_entry(config, list_name, value) if matched else None
            decisive = 0
            for norm in matched:
                if classify_norma(norm.as_record(), reduced).categoria_salida not in SELECTED_CATEGORIES:
                    decisive += 1

            evaluable = counts[REF_RELEVANTE] + counts[REF_NO_RELEVANTE] + counts[REF_NO_RELEVANTE_LECTURA]
            irrelevant = counts[REF_NO_RELEVANTE] + counts[REF_NO_RELEVANTE_LECTURA]
            if evaluable:
                irrelevance = round(irrelevant / evaluable * 100, 1)
            else:
                irrelevance = "Sin base"
            rows.append(
                {
                    "lista": list_name,
                    "valor": value,
                    "condicional": list_name == "KEYWORDS" and entry.normalized in conditional,
                    "coincidencias": len(matched),
                    "relevantes": counts[REF_RELEVANTE],
                    "no_relevantes_decision": counts[REF_NO_RELEVANTE],
                    "no_relevantes_lectura": counts[REF_NO_RELEVANTE_LECTURA],
                    "sin_informacion": counts[REF_SIN_INFORMACION],
                    "evaluables": evaluable,
                    "porcentaje_no_relevante": irrelevance,
                    "decide_seleccion": decisive,
                    "sigue_por_otra_regla": len(matched) - decisive,
                    "candidato_revision": bool(evaluable) and irrelevant == evaluable,
                    "ejemplos": [norm.example() for norm in matched[:MAX_EXAMPLES]],
                }
            )
    return rows


# ---------------------------------------------------------------------------
# Propuestas y comparacion
# ---------------------------------------------------------------------------


def apply_proposal(raw_config: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    """Aplica en memoria una propuesta de cambios y devuelve una configuracion nueva.

    Formato de la propuesta:
        {"descripcion": "...",
         "cambios": [{"lista": "KEYWORDS", "operacion": "eliminar", "valor": "habilitación"},
                     {"lista": "KEYWORDS", "operacion": "agregar", "valor": "nuevo término"},
                     {"lista": "KEYWORDS", "operacion": "reemplazar", "valor": "viejo", "nuevo": "nuevo"}]}
    No modifica raw_config ni ningun archivo.
    """
    changes = proposal.get("cambios")
    if not isinstance(changes, list) or not changes:
        raise ValueError("La propuesta debe incluir una lista 'cambios' con al menos un cambio.")
    proposed = copy.deepcopy(raw_config)
    for index, change in enumerate(changes, start=1):
        list_name = change.get("lista")
        operation = change.get("operacion")
        value = change.get("valor")
        if list_name not in EDITABLE_LISTS:
            raise ValueError(
                f"Cambio {index}: la lista {list_name!r} no se puede modificar en una revision de estrategias."
            )
        if operation not in OPERATIONS:
            raise ValueError(f"Cambio {index}: operacion invalida {operation!r}. Use {', '.join(OPERATIONS)}.")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Cambio {index}: falta el valor.")
        values = proposed.setdefault(list_name, [])
        if operation == "agregar":
            if value in values:
                raise ValueError(f"Cambio {index}: {value!r} ya existe en {list_name}.")
            values.append(value)
        elif operation == "eliminar":
            if value not in values:
                raise ValueError(f"Cambio {index}: {value!r} no existe en {list_name}.")
            values.remove(value)
        else:
            new_value = change.get("nuevo")
            if value not in values:
                raise ValueError(f"Cambio {index}: {value!r} no existe en {list_name}.")
            if not isinstance(new_value, str) or not new_value.strip():
                raise ValueError(f"Cambio {index}: falta el valor 'nuevo' del reemplazo.")
            values[values.index(value)] = new_value

    conditional = set(proposed.get("KEYWORDS_REQUIEREN_ACCION_NORMATIVA", []))
    missing = sorted(conditional - set(proposed.get("KEYWORDS", [])))
    if missing:
        raise ValueError(
            "Toda keyword condicional debe existir tambien en KEYWORDS. Faltan: " + ", ".join(missing)
        )
    return proposed


EFFECT_LABELS = {
    ("entra", REF_RELEVANTE): "relevantes_recuperadas",
    ("sale", REF_RELEVANTE): "relevantes_perdidas",
    ("entra", REF_NO_RELEVANTE): "irrelevantes_anadidas_decision",
    ("entra", REF_NO_RELEVANTE_LECTURA): "irrelevantes_anadidas_lectura",
    ("sale", REF_NO_RELEVANTE): "irrelevantes_evitadas_decision",
    ("sale", REF_NO_RELEVANTE_LECTURA): "irrelevantes_evitadas_lectura",
    ("entra", REF_SIN_INFORMACION): "sin_informacion_anadidas",
    ("sale", REF_SIN_INFORMACION): "sin_informacion_evitadas",
}


def compare_configs(
    period: PeriodData,
    current_raw: dict[str, Any],
    proposed_raw: dict[str, Any],
) -> dict[str, Any]:
    """Compara la seleccion de la configuracion vigente y la propuesta sobre el mismo periodo."""
    current = config_from_dict(current_raw)
    proposed = config_from_dict(proposed_raw)

    effects: dict[str, list[dict[str, str]]] = {label: [] for label in EFFECT_LABELS.values()}
    effects["cambios_relevante_revision_manual"] = []
    rows: list[dict[str, str]] = []
    selected_by_current = {ref: 0 for ref in REFERENCIAS}
    not_selected_by_current = {ref: 0 for ref in REFERENCIAS}

    for norm in period.normas:
        before = classify_norma(norm.as_record(), current).categoria_salida
        after = classify_norma(norm.as_record(), proposed).categoria_salida
        was_selected = before in SELECTED_CATEGORIES
        is_selected = after in SELECTED_CATEGORIES
        (selected_by_current if was_selected else not_selected_by_current)[norm.referencia] += 1

        if was_selected == is_selected:
            if before != after and was_selected:
                effects["cambios_relevante_revision_manual"].append(norm.example())
                rows.append(_comparison_row(norm, before, after, "cambio_relevante_revision_manual"))
            continue
        movement = "entra" if is_selected else "sale"
        label = EFFECT_LABELS[(movement, norm.referencia)]
        effects[label].append(norm.example())
        rows.append(_comparison_row(norm, before, after, label))

    # Normas que coincidian con un valor eliminado o reemplazado y siguen seleccionadas.
    still_selected = _still_selected_by_other_rule(period, current_raw, proposed_raw, current, proposed)

    summary = {label: len(items) for label, items in effects.items()}
    bases = {
        "relevantes_seleccionadas_vigente": selected_by_current[REF_RELEVANTE],
        "relevantes_no_seleccionadas_vigente": not_selected_by_current[REF_RELEVANTE],
        "irrelevantes_seleccionadas_vigente": selected_by_current[REF_NO_RELEVANTE]
        + selected_by_current[REF_NO_RELEVANTE_LECTURA],
        "irrelevantes_no_seleccionadas_vigente": not_selected_by_current[REF_NO_RELEVANTE]
        + not_selected_by_current[REF_NO_RELEVANTE_LECTURA],
    }
    return {
        "resumen": summary,
        "bases": bases,
        "porcentajes": _comparison_percentages(summary, bases),
        "ejemplos": {label: items[:MAX_EXAMPLES] for label, items in effects.items()},
        "siguen_por_otra_regla": still_selected,
        "detalle": rows,
    }


def _comparison_row(norm: StoredNorm, before: str, after: str, effect: str) -> dict[str, str]:
    return {
        "efecto": effect,
        "nombre": norm.nombre,
        "numero_boletin": norm.numero_boletin,
        "fecha_publicacion": norm.fecha_publicacion,
        "referencia": norm.referencia,
        "categoria_vigente": before,
        "categoria_propuesta": after,
        "sumario": norm.sumario,
        "url_norma": norm.url_norma,
    }


def _comparison_percentages(summary: dict[str, int], bases: dict[str, int]) -> dict[str, Any]:
    def ratio(part: int, base: int) -> Any:
        return round(part / base * 100, 1) if base else "Sin base"

    return {
        "relevantes_recuperadas": ratio(summary["relevantes_recuperadas"], bases["relevantes_no_seleccionadas_vigente"]),
        "relevantes_perdidas": ratio(summary["relevantes_perdidas"], bases["relevantes_seleccionadas_vigente"]),
        "irrelevantes_evitadas": ratio(
            summary["irrelevantes_evitadas_decision"] + summary["irrelevantes_evitadas_lectura"],
            bases["irrelevantes_seleccionadas_vigente"],
        ),
        "irrelevantes_anadidas": ratio(
            summary["irrelevantes_anadidas_decision"] + summary["irrelevantes_anadidas_lectura"],
            bases["irrelevantes_no_seleccionadas_vigente"],
        ),
    }


def _still_selected_by_other_rule(
    period: PeriodData,
    current_raw: dict[str, Any],
    proposed_raw: dict[str, Any],
    current: DetectorConfig,
    proposed: DetectorConfig,
) -> list[dict[str, Any]]:
    """Para cada valor retirado, cuantas normas que lo usaban siguen seleccionadas."""
    output = []
    conditional = {entry.normalized for entry in current.keywords_requieren_accion_normativa}
    for list_name in ("KEYWORDS", "LISTA_NORMAS_CURADAS", "LISTA_ORGANISMOS_PRIORIDAD"):
        removed = [value for value in current_raw.get(list_name, []) if value not in proposed_raw.get(list_name, [])]
        for value in removed:
            entry = _find_entry(current, list_name, value)
            matched = [
                norm
                for norm in period.normas
                if passes_structural_filter(norm.as_record(), current)
                and _term_matches(norm, list_name, entry, current, conditional)
                and classify_norma(norm.as_record(), current).categoria_salida in SELECTED_CATEGORIES
            ]
            remaining = [
                norm
                for norm in matched
                if classify_norma(norm.as_record(), proposed).categoria_salida in SELECTED_CATEGORIES
            ]
            output.append(
                {
                    "lista": list_name,
                    "valor": value,
                    "seleccionadas_por_el_valor": len(matched),
                    "siguen_seleccionadas": len(remaining),
                    "ejemplos": [norm.example() for norm in remaining[:MAX_EXAMPLES]],
                }
            )
    return output


def _find_entry(config: DetectorConfig, list_name: str, value: str) -> Any:
    if list_name == "KEYWORDS":
        source = config.keywords
        return next(entry for entry in source if entry.original == value)
    if list_name == "LISTA_NORMAS_CURADAS":
        return next(pattern for pattern in config.normas_curadas if pattern.pattern == value)
    return next(entry for entry in config.organismos_prioridad if entry.original == value)
