#!/usr/bin/env python3
"""Valida la configuración JSON del detector BO CABA sin modificar archivos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata


LIST_FIELDS = (
    "PODERES_INCLUIDOS",
    "TIPOS_NORMA_INCLUIDOS",
    "KEYWORDS",
    "KEYWORDS_REQUIEREN_ACCION_NORMATIVA",
    "VERBOS_ACCION",
    "LISTA_NORMAS_CURADAS",
    "LISTA_ORGANISMOS_PRIORIDAD",
)

REGEX_FIELDS = ("VERBOS_ACCION", "LISTA_NORMAS_CURADAS")


def normalize_text(value: str) -> str:
    """Replica la normalización relevante para detectar duplicados."""
    normalized = unicodedata.normalize("NFD", value.lower().strip())
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"\s+", " ", normalized).strip()


def load_json(path: Path) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"No existe el archivo: {path}"]
    except UnicodeDecodeError as exc:
        return None, [f"El archivo no es UTF-8 válido: {exc}"]
    except json.JSONDecodeError as exc:
        return None, [f"JSON inválido en línea {exc.lineno}, columna {exc.colno}: {exc.msg}"]

    if not isinstance(data, dict):
        errors.append("La raíz del JSON debe ser un objeto.")
        return None, errors
    return data, errors


def validate_lists(data: dict) -> list[str]:
    errors: list[str] = []
    for field in LIST_FIELDS:
        if field not in data:
            errors.append(f"Falta el campo requerido {field}.")
            continue

        values = data[field]
        if not isinstance(values, list):
            errors.append(f"{field} debe ser una lista.")
            continue

        for index, value in enumerate(values):
            if not isinstance(value, str):
                errors.append(f"{field}[{index}] debe ser texto.")
            elif not value.strip():
                errors.append(f"{field}[{index}] no puede estar vacío.")
            elif value != value.strip():
                errors.append(f"{field}[{index}] contiene espacios exteriores: {value!r}.")
    return errors


def validate_duplicates(data: dict) -> list[str]:
    errors: list[str] = []
    for field in LIST_FIELDS:
        values = data.get(field)
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            continue

        seen: dict[str, str] = {}
        for value in values:
            key = value.strip().casefold() if field in REGEX_FIELDS else normalize_text(value)
            if key in seen:
                errors.append(
                    f"{field} contiene un duplicado: {seen[key]!r} y {value!r}."
                )
            else:
                seen[key] = value
    return errors


def validate_regexes(data: dict) -> list[str]:
    errors: list[str] = []
    for field in REGEX_FIELDS:
        values = data.get(field)
        if not isinstance(values, list):
            continue
        for index, pattern in enumerate(values):
            if not isinstance(pattern, str):
                continue
            try:
                re.compile(pattern, flags=re.IGNORECASE)
            except re.error as exc:
                errors.append(f"Regex inválida en {field}[{index}] {pattern!r}: {exc}.")
    return errors


def validate_conditional_subset(data: dict) -> list[str]:
    keywords = data.get("KEYWORDS")
    conditional = data.get("KEYWORDS_REQUIEREN_ACCION_NORMATIVA")
    if not isinstance(keywords, list) or not isinstance(conditional, list):
        return []
    if not all(isinstance(value, str) for value in keywords + conditional):
        return []

    keyword_keys = {normalize_text(value) for value in keywords}
    missing = [value for value in conditional if normalize_text(value) not in keyword_keys]
    return [
        "Cada keyword condicional debe existir también en KEYWORDS; "
        f"faltan: {', '.join(repr(value) for value in missing)}."
    ] if missing else []


def validate_config(path: Path) -> tuple[dict | None, list[str]]:
    data, errors = load_json(path)
    if data is None:
        return None, errors

    errors.extend(validate_lists(data))
    errors.extend(validate_duplicates(data))
    errors.extend(validate_regexes(data))
    errors.extend(validate_conditional_subset(data))
    return data, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida config/config_keywords.json sin modificarlo."
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Raíz del repositorio (por defecto, el directorio actual).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Ruta alternativa al JSON; prevalece sobre la raíz del repositorio.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.config or Path(args.repo) / "config" / "config_keywords.json"
    config_path = config_path.resolve()
    data, errors = validate_config(config_path)

    if errors:
        print(f"Configuración inválida: {config_path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    assert data is not None
    print(f"Configuración válida: {config_path}")
    for field in LIST_FIELDS:
        print(f"- {field}: {len(data[field])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
