from __future__ import annotations

from typing import Any


def flatten_normas_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten API payloads into one record per norma."""
    normas_tree = _extract_normas_tree(payload)
    boletin = payload.get("boletin") if isinstance(payload.get("boletin"), dict) else {}

    records: list[dict[str, Any]] = []
    for poder, tipos in normas_tree.items():
        if not isinstance(tipos, dict):
            continue
        for tipo_norma, organismos in tipos.items():
            if not isinstance(organismos, dict):
                continue
            for organismo, normas in organismos.items():
                if not isinstance(normas, list):
                    continue
                for norma in normas:
                    if not isinstance(norma, dict):
                        continue
                    records.append(_build_record(norma, poder, tipo_norma, organismo, boletin))
    return records


def _extract_normas_tree(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        payload.get("normas"),
        payload.get("data"),
    ]

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        nested = candidate.get("normas")
        if isinstance(nested, dict):
            return nested
        if _looks_like_normas_tree(candidate):
            return candidate

    if _looks_like_normas_tree(payload):
        return payload

    return {}


def _looks_like_normas_tree(value: dict[str, Any]) -> bool:
    return any(str(key).lower().startswith("poder ") for key in value)


def _build_record(
    norma: dict[str, Any],
    poder: str,
    tipo_norma: str,
    organismo: str,
    boletin: dict[str, Any],
) -> dict[str, Any]:
    return {
        "poder": poder,
        "tipo_norma": tipo_norma,
        "organismo": organismo,
        "nombre": norma.get("nombre", ""),
        "sumario": norma.get("sumario", ""),
        "id_norma": norma.get("id_norma"),
        "id_sdin": norma.get("id_sdin"),
        "url_norma": norma.get("url_norma", ""),
        "anexos": _normalize_anexos(norma.get("anexos")),
        "numero_boletin": boletin.get("numero") or boletin.get("numero2"),
        "fecha_publicacion": boletin.get("fecha_publicacion"),
        "url_boletin": boletin.get("url_boletin"),
    }


def _normalize_anexos(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    anexos: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        url = item.get("filenet_firmado") or item.get("url") or item.get("url_anexo") or ""
        name = item.get("nombre_anexo") or item.get("nombre") or ""
        anexos.append({"nombre_anexo": str(name), "url": str(url)})
    return anexos

