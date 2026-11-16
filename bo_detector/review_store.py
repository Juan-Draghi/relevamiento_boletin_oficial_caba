from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import re
import threading
from typing import Any

from .classifier import (
    DESCARTADA_FILTRO_ESTRUCTURAL,
    NO_RELEVANTE,
    RELEVANTE,
    REVISION_MANUAL,
)


SCHEMA_VERSION = 1

SIN_REVISAR = "SIN_REVISAR"
RELEVANTE_CONFIRMADA = "RELEVANTE_CONFIRMADA"
NO_RELEVANTE_CONFIRMADA = "NO_RELEVANTE_CONFIRMADA"
DECISIONES_MANUALES = {
    SIN_REVISAR,
    RELEVANTE_CONFIRMADA,
    NO_RELEVANTE_CONFIRMADA,
}

CONTROL_PENDIENTE = "PENDIENTE"
CONTROL_PARCIAL = "PARCIAL"
CONTROL_COMPLETO = "COMPLETO"
CONTROLES_COMPLEMENTARIOS = {
    CONTROL_PENDIENTE,
    CONTROL_PARCIAL,
    CONTROL_COMPLETO,
}

WEEK_KEY_RE = re.compile(r"^\d{4}-W\d{2}$")
_STORE_LOCK = threading.RLock()


def normalize_publication_date(value: Any) -> date:
    text = str(value or "").strip()
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"Fecha de publicacion invalida: {text or '(vacia)'}")


def week_key_for_date(publication_date: date) -> str:
    iso_year, iso_week, _ = publication_date.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def week_bounds(week_key: str) -> tuple[date, date]:
    validate_week_key(week_key)
    iso_year = int(week_key[:4])
    iso_week = int(week_key[-2:])
    try:
        start = date.fromisocalendar(iso_year, iso_week, 1)
    except ValueError as exc:
        raise ValueError(f"Semana ISO invalida: {week_key}") from exc
    return start, start + timedelta(days=6)


def validate_week_key(week_key: str) -> None:
    if not WEEK_KEY_RE.fullmatch(str(week_key or "")):
        raise ValueError(f"Clave de semana invalida: {week_key!r}")


def record_key(record: dict[str, Any]) -> str:
    id_norma = _clean_identifier(record.get("id_norma"))
    if id_norma:
        return f"id_norma:{id_norma}"

    id_sdin = _clean_identifier(record.get("id_sdin"))
    if id_sdin:
        return f"id_sdin:{id_sdin}"

    fallback_values = [
        record.get("numero_boletin"),
        record.get("fecha_publicacion"),
        record.get("poder"),
        record.get("tipo_norma"),
        record.get("organismo"),
        record.get("nombre"),
        record.get("url_norma"),
        record.get("sumario"),
    ]
    normalized = "|".join(" ".join(str(value or "").split()).casefold() for value in fallback_values)
    return f"huella:{sha256(normalized.encode('utf-8')).hexdigest()[:24]}"


def upsert_analysis(
    data_dir: Path,
    summary: dict[str, Any],
    classified_records: list[dict[str, Any]],
    now: datetime | None = None,
) -> dict[str, Any]:
    publication_date = normalize_publication_date(summary.get("fecha_publicacion"))
    week_key = week_key_for_date(publication_date)
    bulletin_key = _bulletin_key(summary.get("numero_boletin"), publication_date)
    timestamp = _timestamp(now)

    with _STORE_LOCK:
        document = load_week(data_dir, week_key)
        bulletins = document["boletines"]
        bulletin = bulletins.get(bulletin_key)
        if not isinstance(bulletin, dict):
            bulletin = {
                "numero_boletin": str(summary.get("numero_boletin") or ""),
                "fecha_publicacion": publication_date.isoformat(),
                "primera_ejecucion": timestamp,
                "ultima_ejecucion": timestamp,
                "control_complementario": CONTROL_PENDIENTE,
                "observaciones": "",
                "normas": {},
            }
            bulletins[bulletin_key] = bulletin

        bulletin["ultima_ejecucion"] = timestamp
        normas = bulletin.setdefault("normas", {})

        for record in classified_records:
            key = record_key(record)
            existing = normas.get(key) if isinstance(normas.get(key), dict) else {}
            normas[key] = _serialize_record(record, key, existing)

        _save_week(data_dir, week_key, document)
        return {
            "semana": week_key,
            "boletin_clave": bulletin_key,
            "control_complementario": bulletin["control_complementario"],
            "observaciones_boletin": bulletin.get("observaciones") or "",
            "normas": {
                key: {
                    "categoria_automatica_original": item["categoria_automatica_original"],
                    "decision_manual": item["decision_manual"],
                    "observacion_revision": item["observacion_revision"],
                }
                for key, item in normas.items()
            },
        }


def update_norm_review(
    data_dir: Path,
    week_key: str,
    bulletin_key: str,
    norm_key: str,
    decision: str,
    observation: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    if decision not in DECISIONES_MANUALES:
        raise ValueError(f"Decision manual invalida: {decision}")

    with _STORE_LOCK:
        document = load_week(data_dir, week_key)
        bulletin = _require_bulletin(document, bulletin_key)
        norm = _require_norm(bulletin, norm_key)
        observation = str(observation or "").strip()

        is_false_negative = (
            norm["categoria_automatica_original"]
            in {NO_RELEVANTE, DESCARTADA_FILTRO_ESTRUCTURAL}
            and decision == RELEVANTE_CONFIRMADA
        )
        if is_false_negative and not observation:
            raise ValueError("La confirmacion de un falso negativo requiere una observacion breve.")

        norm["decision_manual"] = decision
        norm["observacion_revision"] = observation
        norm["revisado_en"] = None if decision == SIN_REVISAR else _timestamp(now)
        _save_week(data_dir, week_key, document)
        return {
            "decision_manual": decision,
            "observacion_revision": observation,
            "es_falso_negativo": is_false_negative,
        }


def pending_primary_decisions(bulletin: dict[str, Any]) -> list[dict[str, str]]:
    """Normas RELEVANTE o REVISION_MANUAL del boletin que siguen sin decision profesional."""
    norms = bulletin.get("normas") if isinstance(bulletin.get("normas"), dict) else {}
    pending = []
    for key, norm in norms.items():
        category = str(norm.get("categoria_automatica_original") or "")
        decision = str(norm.get("decision_manual") or SIN_REVISAR)
        if category in {RELEVANTE, REVISION_MANUAL} and decision == SIN_REVISAR:
            pending.append(
                {
                    "clave": key,
                    "nombre": str(norm.get("nombre") or key),
                    "categoria_automatica_original": category,
                }
            )
    return sorted(pending, key=lambda item: (item["categoria_automatica_original"], item["nombre"]))


def update_bulletin_review(
    data_dir: Path,
    week_key: str,
    bulletin_key: str,
    control: str,
    observations: str = "",
    confirm_pending: bool = False,
) -> dict[str, Any]:
    """Guarda el control complementario.

    Si se marca COMPLETO y quedan alertas sin decision, no guarda y devuelve
    la lista de pendientes, salvo que confirm_pending sea True.
    """
    if control not in CONTROLES_COMPLEMENTARIOS:
        raise ValueError(f"Control complementario invalido: {control}")

    with _STORE_LOCK:
        document = load_week(data_dir, week_key)
        bulletin = _require_bulletin(document, bulletin_key)
        pending = pending_primary_decisions(bulletin)
        if control == CONTROL_COMPLETO and pending and not confirm_pending:
            return {
                "guardado": False,
                "control_complementario": bulletin.get("control_complementario") or CONTROL_PENDIENTE,
                "pendientes": pending,
            }
        bulletin["control_complementario"] = control
        bulletin["observaciones"] = str(observations or "").strip()
        _save_week(data_dir, week_key, document)
        return {
            "guardado": True,
            "control_complementario": control,
            "observaciones": bulletin["observaciones"],
            "pendientes": pending,
        }


def update_week_notes(
    data_dir: Path,
    week_key: str,
    adjustments: list[str],
    observations: str = "",
) -> dict[str, Any]:
    with _STORE_LOCK:
        document = load_week(data_dir, week_key)
        clean_adjustments = []
        seen = set()
        for value in adjustments:
            item = str(value or "").strip()
            if item and item not in seen:
                clean_adjustments.append(item)
                seen.add(item)
        document["ajustes_derivados"] = clean_adjustments
        document["observaciones"] = str(observations or "").strip()
        _save_week(data_dir, week_key, document)
        return {
            "ajustes_derivados": clean_adjustments,
            "observaciones": document["observaciones"],
        }


def load_week(data_dir: Path, week_key: str) -> dict[str, Any]:
    validate_week_key(week_key)
    path = Path(data_dir) / f"{week_key}.json"
    if not path.exists():
        return _empty_week(week_key)

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"El archivo {path.name} no contiene JSON valido.") from exc
    if not isinstance(document, dict) or document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"El archivo {path.name} usa un esquema no compatible.")
    if not isinstance(document.get("boletines"), dict):
        raise ValueError(f"El archivo {path.name} no contiene un objeto 'boletines' valido.")
    return document


def list_week_keys(data_dir: Path) -> list[str]:
    directory = Path(data_dir)
    if not directory.exists():
        return []
    keys = [path.stem for path in directory.glob("????-W??.json") if WEEK_KEY_RE.fullmatch(path.stem)]
    return sorted(set(keys), reverse=True)


def calculate_week_indicators(document: dict[str, Any]) -> dict[str, Any]:
    bulletins = document.get("boletines") if isinstance(document.get("boletines"), dict) else {}
    indicators = _calculate_indicators(list(bulletins.items()), document.get("periodo") or {})
    indicators["ajustes_derivados"] = document.get("ajustes_derivados") or []
    indicators["observaciones"] = document.get("observaciones") or ""
    return indicators


def data_date_range(data_dir: Path) -> dict[str, str] | None:
    """Primera y ultima fecha de publicacion registradas en los JSON semanales."""
    week_keys = sorted(list_week_keys(data_dir))
    dates: list[str] = []
    for week_key in (week_keys[:1] + week_keys[-1:]) if week_keys else []:
        for bulletin in load_week(data_dir, week_key)["boletines"].values():
            if isinstance(bulletin, dict) and bulletin.get("fecha_publicacion"):
                dates.append(str(bulletin["fecha_publicacion"]))
    if not dates:
        return None
    return {"desde": min(dates), "hasta": max(dates)}


def load_period_bulletins(
    data_dir: Path,
    start: date,
    end: date,
) -> list[tuple[str, dict[str, Any]]]:
    """Boletines cuya fecha de publicacion cae entre start y end (inclusive).

    Lee solo las semanas que se superponen con el rango. No modifica archivos.
    """
    selected: dict[str, dict[str, Any]] = {}
    for week_key in sorted(list_week_keys(data_dir)):
        week_start, week_end = week_bounds(week_key)
        if week_end < start or week_start > end:
            continue
        for bulletin_key, bulletin in load_week(data_dir, week_key)["boletines"].items():
            if not isinstance(bulletin, dict) or bulletin_key in selected:
                continue
            try:
                publication_date = normalize_publication_date(bulletin.get("fecha_publicacion"))
            except ValueError:
                continue
            if start <= publication_date <= end:
                selected[bulletin_key] = bulletin
    return list(selected.items())


def calculate_period_indicators(data_dir: Path, start: date, end: date) -> dict[str, Any]:
    """Indicadores de un rango de fechas, contando cada norma una sola vez.

    Una norma repetida en varios boletines se computa en su primera aparicion.
    Los porcentajes se calculan sobre los totales del periodo, nunca
    promediando valores semanales.
    """
    if start > end:
        raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")

    bulletins = load_period_bulletins(data_dir, start, end)
    indicators = _calculate_indicators(
        bulletins,
        {"clave": "periodo", "desde": start.isoformat(), "hasta": end.isoformat()},
    )

    available = data_date_range(data_dir)
    warnings: list[str] = []
    if available:
        if start.isoformat() < available["desde"]:
            warnings.append(f"No hay registros anteriores al {_display_date(available['desde'])}.")
        if end.isoformat() > available["hasta"]:
            warnings.append(f"No hay registros posteriores al {_display_date(available['hasta'])}.")
    indicators["cobertura"] = {
        "rango_datos": available,
        "boletines": len(bulletins),
        "sin_registros": not bulletins,
        "avisos": warnings,
    }
    indicators["ajustes_derivados"] = []
    indicators["observaciones"] = ""
    return indicators


def _calculate_indicators(
    bulletin_items: list[tuple[str, dict[str, Any]]],
    period: dict[str, Any],
) -> dict[str, Any]:
    """Calcula los indicadores de un conjunto de boletines.

    Cada norma se cuenta una sola vez, en el primer boletin en que aparece.
    Si una norma repetida tiene la decision guardada en otra copia, se usa esa
    decision. Si las copias tienen decisiones distintas, se informa como
    contradiccion y se usa la decision registrada mas reciente.
    """
    bulletins = {key: value for key, value in bulletin_items if isinstance(value, dict)}
    ordered_bulletins = sorted(
        bulletins.items(),
        key=lambda item: (str(item[1].get("fecha_publicacion") or ""), item[0]),
    )

    merged_norms = _merge_norm_copies(ordered_bulletins)

    category_counts: Counter[str] = Counter()
    publication_dates: set[str] = set()
    relevant_confirmed = 0
    relevant_from_manual_review = 0
    omission_count = 0
    validated_count = 0
    automatic_relevant_validated = 0
    automatic_true_positives = 0
    automatic_false_positives = 0
    manual_review_validated = 0
    manual_review_relevant = 0
    pending: list[dict[str, Any]] = []

    for item in merged_norms.values():
        category = item["categoria"]
        decision = item["decision"]
        category_counts[category] += 1

        if decision in {RELEVANTE_CONFIRMADA, NO_RELEVANTE_CONFIRMADA}:
            validated_count += 1
            if category == RELEVANTE:
                automatic_relevant_validated += 1
                if decision == RELEVANTE_CONFIRMADA:
                    automatic_true_positives += 1
                else:
                    automatic_false_positives += 1
            elif category == REVISION_MANUAL:
                manual_review_validated += 1
                if decision == RELEVANTE_CONFIRMADA:
                    manual_review_relevant += 1
        elif item["pendiente"]:
            pending.append(
                {
                    "nombre": item["nombre"],
                    "categoria_automatica_original": category,
                    "numero_boletin": item["numero_boletin"],
                    "fecha_publicacion": item["fecha_publicacion"],
                    "url_norma": item["url_norma"],
                }
            )

        if decision == RELEVANTE_CONFIRMADA:
            relevant_confirmed += 1
            if category == REVISION_MANUAL:
                relevant_from_manual_review += 1
            elif category in {NO_RELEVANTE, DESCARTADA_FILTRO_ESTRUCTURAL}:
                omission_count += 1

    pending_keys = {key for key, item in merged_norms.items() if item["pendiente"]}
    bulletin_rows: list[dict[str, Any]] = []
    complete_with_pending: list[dict[str, Any]] = []
    for bulletin_key, bulletin in ordered_bulletins:
        publication_date = str(bulletin.get("fecha_publicacion") or "")
        if publication_date:
            publication_dates.add(publication_date)
        norms = bulletin.get("normas") if isinstance(bulletin.get("normas"), dict) else {}
        control = bulletin.get("control_complementario") or CONTROL_PENDIENTE
        # Las filas por boletin muestran las decisiones guardadas en ese boletin.
        local_relevant = 0
        local_omissions = 0
        for norm in norms.values():
            if isinstance(norm, dict) and norm.get("decision_manual") == RELEVANTE_CONFIRMADA:
                local_relevant += 1
                if norm.get("categoria_automatica_original") in {NO_RELEVANTE, DESCARTADA_FILTRO_ESTRUCTURAL}:
                    local_omissions += 1
        bulletin_pending = len(pending_keys.intersection(norms.keys()))
        if control == CONTROL_COMPLETO and bulletin_pending:
            complete_with_pending.append(
                {
                    "numero_boletin": bulletin.get("numero_boletin") or "",
                    "fecha_publicacion": publication_date,
                    "pendientes": bulletin_pending,
                }
            )
        bulletin_rows.append(
            {
                "clave": bulletin_key,
                "numero_boletin": bulletin.get("numero_boletin") or "",
                "fecha_publicacion": publication_date,
                "control_complementario": control,
                "normas_procesadas": len(norms),
                "relevantes_confirmadas": local_relevant,
                "omisiones_identificadas": local_omissions,
            }
        )

    weekly_control = _weekly_control(bulletins)
    total_processed = len(merged_norms)
    no_activity = "No utilizado"
    pending.sort(key=lambda entry: (entry["fecha_publicacion"], entry["nombre"]))
    contradictions = [
        {"nombre": item["nombre"], "decisiones": item["decisiones_registradas"]}
        for item in merged_norms.values()
        if item["contradiccion"]
    ]

    # El porcentaje de omisiones es provisional mientras la revision no este cerrada.
    provisional_reasons: list[str] = []
    if bulletins and weekly_control != CONTROL_COMPLETO:
        provisional_reasons.append("Hay boletines sin control complementario completo.")
    if pending:
        provisional_reasons.append("Hay alertas sin decisión profesional.")

    omission_percentage: float | str
    if relevant_confirmed:
        omission_percentage = round(omission_count / relevant_confirmed * 100, 1)
    else:
        omission_percentage = "No calculable"

    performance_indicators = {
        "cobertura_validacion": (
            round(validated_count / total_processed * 100, 1)
            if total_processed
            else no_activity
        ),
        "precision_automatica": (
            round(automatic_true_positives / automatic_relevant_validated * 100, 1)
            if automatic_relevant_validated
            else "N/D"
        ),
        "tasa_falsos_positivos": (
            round(automatic_false_positives / automatic_relevant_validated * 100, 1)
            if automatic_relevant_validated
            else "N/D"
        ),
        "tasa_revision_manual": (
            round(category_counts.get(REVISION_MANUAL, 0) / total_processed * 100, 1)
            if total_processed
            else no_activity
        ),
        "rendimiento_revision_manual": (
            round(manual_review_relevant / manual_review_validated * 100, 1)
            if manual_review_validated
            else "N/D"
        ),
        "reduccion_lectura": (
            round(
                (
                    category_counts.get(NO_RELEVANTE, 0)
                    + category_counts.get(DESCARTADA_FILTRO_ESTRUCTURAL, 0)
                )
                / total_processed
                * 100,
                1,
            )
            if total_processed
            else no_activity
        ),
        "porcentaje_omisiones": omission_percentage,
        "bases_desempeno": {
            "normas_validadas": validated_count,
            "alertas_automaticas_validadas": automatic_relevant_validated,
            "casos_revision_manual_validados": manual_review_validated,
            "relevantes_confirmadas": relevant_confirmed,
        },
    }

    return {
        "periodo": period,
        "dias_uso": len(publication_dates),
        "normas_procesadas": total_processed,
        "relevantes": category_counts.get(RELEVANTE, 0),
        "revision_manual": category_counts.get(REVISION_MANUAL, 0),
        "no_relevantes": category_counts.get(NO_RELEVANTE, 0),
        "descartadas": category_counts.get(DESCARTADA_FILTRO_ESTRUCTURAL, 0),
        "relevantes_confirmadas_total": relevant_confirmed,
        "relevantes_desde_revision_manual": relevant_from_manual_review,
        "omisiones_identificadas": omission_count,
        "omisiones_provisional": bool(provisional_reasons),
        "motivos_provisional": provisional_reasons,
        "control_complementario": weekly_control,
        "avisos_consistencia": {
            "pendientes": pending,
            "completos_con_pendientes": complete_with_pending,
            "contradicciones": contradictions,
        },
        "boletines": bulletin_rows,
        **performance_indicators,
    }


def _merge_norm_copies(
    ordered_bulletins: list[tuple[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    """Une las copias de una misma norma publicada en varios boletines.

    Devuelve un elemento por clave de norma, con los datos de la primera
    aparicion y la decision registrada en cualquiera de sus copias.
    """
    merged: dict[str, dict[str, Any]] = {}
    for _bulletin_key, bulletin in ordered_bulletins:
        norms = bulletin.get("normas") if isinstance(bulletin.get("normas"), dict) else {}
        for key, norm in norms.items():
            if not isinstance(norm, dict):
                continue
            item = merged.get(key)
            if item is None:
                item = {
                    "categoria": str(norm.get("categoria_automatica_original") or ""),
                    "nombre": str(norm.get("nombre") or key),
                    "url_norma": str(norm.get("url_norma") or ""),
                    "numero_boletin": str(bulletin.get("numero_boletin") or ""),
                    "fecha_publicacion": str(bulletin.get("fecha_publicacion") or ""),
                    "decisiones_registradas": [],
                }
                merged[key] = item
            decision = str(norm.get("decision_manual") or SIN_REVISAR)
            if decision != SIN_REVISAR:
                item["decisiones_registradas"].append(
                    {
                        "numero_boletin": str(bulletin.get("numero_boletin") or ""),
                        "fecha_publicacion": str(bulletin.get("fecha_publicacion") or ""),
                        "decision_manual": decision,
                        "revisado_en": str(norm.get("revisado_en") or ""),
                    }
                )

    for item in merged.values():
        recorded = item["decisiones_registradas"]
        if recorded:
            latest = max(recorded, key=lambda entry: entry["revisado_en"])
            item["decision"] = latest["decision_manual"]
        else:
            item["decision"] = SIN_REVISAR
        item["contradiccion"] = len({entry["decision_manual"] for entry in recorded}) > 1
        item["pendiente"] = (
            item["decision"] == SIN_REVISAR and item["categoria"] in {RELEVANTE, REVISION_MANUAL}
        )
    return merged


def _empty_week(week_key: str) -> dict[str, Any]:
    start, end = week_bounds(week_key)
    return {
        "schema_version": SCHEMA_VERSION,
        "periodo": {
            "clave": week_key,
            "desde": start.isoformat(),
            "hasta": end.isoformat(),
        },
        "boletines": {},
        "ajustes_derivados": [],
        "observaciones": "",
    }


def _serialize_record(
    record: dict[str, Any],
    key: str,
    existing: dict[str, Any],
) -> dict[str, Any]:
    original_category = existing.get("categoria_automatica_original") or record.get("categoria_salida") or ""
    return {
        "clave": key,
        "id_norma": record.get("id_norma"),
        "id_sdin": record.get("id_sdin"),
        "nombre": record.get("nombre") or "",
        "poder": record.get("poder") or "",
        "tipo_norma": record.get("tipo_norma") or "",
        "organismo": record.get("organismo") or "",
        "sumario": record.get("sumario") or "",
        "url_norma": record.get("url_norma") or "",
        "motivo_deteccion": record.get("motivo_deteccion") or [],
        "categoria_automatica_original": original_category,
        "decision_manual": existing.get("decision_manual") or SIN_REVISAR,
        "observacion_revision": existing.get("observacion_revision") or "",
        "revisado_en": existing.get("revisado_en"),
    }


def _weekly_control(bulletins: dict[str, Any]) -> str:
    if not bulletins:
        return "No utilizado"
    controls = {
        str(bulletin.get("control_complementario") or CONTROL_PENDIENTE)
        for bulletin in bulletins.values()
        if isinstance(bulletin, dict)
    }
    if controls == {CONTROL_COMPLETO}:
        return CONTROL_COMPLETO
    if controls == {CONTROL_PENDIENTE}:
        return "N/D"
    return CONTROL_PARCIAL


def _save_week(data_dir: Path, week_key: str, document: dict[str, Any]) -> None:
    directory = Path(data_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{week_key}.json"
    temporary_path = directory / f"{week_key}.json.tmp"
    temporary_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _require_bulletin(document: dict[str, Any], bulletin_key: str) -> dict[str, Any]:
    bulletin = document.get("boletines", {}).get(bulletin_key)
    if not isinstance(bulletin, dict):
        raise ValueError(f"Boletin no encontrado: {bulletin_key}")
    return bulletin


def _require_norm(bulletin: dict[str, Any], norm_key: str) -> dict[str, Any]:
    norm = bulletin.get("normas", {}).get(norm_key)
    if not isinstance(norm, dict):
        raise ValueError(f"Norma no encontrada: {norm_key}")
    return norm


def _bulletin_key(number: Any, publication_date: date) -> str:
    clean_number = _clean_identifier(number)
    return f"boletin:{clean_number}" if clean_number else f"fecha:{publication_date.isoformat()}"


def _clean_identifier(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"", "none", "null"} else text


def _display_date(iso_value: str) -> str:
    parts = str(iso_value or "").split("-")
    return f"{parts[2]}/{parts[1]}/{parts[0]}" if len(parts) == 3 else str(iso_value or "")


def _timestamp(value: datetime | None) -> str:
    current = value or datetime.now().astimezone()
    if current.tzinfo is None:
        current = current.astimezone()
    return current.isoformat(timespec="seconds")
