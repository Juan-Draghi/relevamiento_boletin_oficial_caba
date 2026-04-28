from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import os
import re
import sys
import threading
import uuid
import webbrowser
from typing import Any

from flask import Flask, jsonify, render_template, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bo_detector.api import BoletinAPIClient, BoletinAPIError
from bo_detector.classifier import (
    DESCARTADA_FILTRO_ESTRUCTURAL,
    NO_RELEVANTE,
    RELEVANTE,
    REVISION_MANUAL,
)
from bo_detector.config import DEFAULT_CONFIG_PATH, load_config
from bo_detector.flatten import flatten_normas_payload
from bo_detector.pipeline import classify_records
from bo_detector.text import normalize_text


def get_bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


BUNDLE_ROOT = get_bundle_root()
TEMPLATES_DIR = BUNDLE_ROOT / "templates"
STATIC_DIR = BUNDLE_ROOT / "static"
CONFIG_PATH = DEFAULT_CONFIG_PATH
EDITABLE_CONFIG_FIELDS = (
    "KEYWORDS",
    "LISTA_NORMAS_CURADAS",
    "LISTA_ORGANISMOS_PRIORIDAD",
)

app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))
ANALYSIS_JOBS: dict[str, dict[str, Any]] = {}
ANALYSIS_JOBS_LOCK = threading.Lock()


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def set_job_state(job_id: str, **updates: Any) -> None:
    with ANALYSIS_JOBS_LOCK:
        if job_id in ANALYSIS_JOBS:
            ANALYSIS_JOBS[job_id].update(updates)


def create_analysis_job(
    parametro: str,
    include_no_relevante: bool,
    include_descartadas: bool,
) -> str:
    job_id = uuid.uuid4().hex
    with ANALYSIS_JOBS_LOCK:
        ANALYSIS_JOBS[job_id] = {
            "id": job_id,
            "status": "queued",
            "message": "Preparando consulta a la API...",
            "progress_percent": 2,
            "selected_parametro": parametro,
            "results": [],
            "summary": {},
        }

    thread = threading.Thread(
        target=run_analysis_job,
        args=(job_id, parametro, include_no_relevante, include_descartadas),
        daemon=True,
    )
    thread.start()
    return job_id


def run_analysis_job(
    job_id: str,
    parametro: str,
    include_no_relevante: bool,
    include_descartadas: bool,
) -> None:
    try:
        set_job_state(job_id, status="running", message="Cargando configuracion...", progress_percent=8)
        config = load_config()

        set_job_state(job_id, message="Consultando Boletin Oficial CABA...", progress_percent=18)
        payload = BoletinAPIClient().obtener_boletin(parametro=parametro, carga_datos=True)

        set_job_state(job_id, message="Aplanando estructura de normas...", progress_percent=45)
        records = flatten_normas_payload(payload)

        set_job_state(job_id, message="Aplicando reglas de deteccion...", progress_percent=65)
        classified_all = classify_records(
            records,
            config=config,
            include_no_relevante=True,
            include_descartadas=True,
        )
        category_counts = Counter(item["categoria_salida"] for item in classified_all)

        visible_results = [
            item
            for item in classified_all
            if _should_include_item(item["categoria_salida"], include_no_relevante, include_descartadas)
        ]

        summary = build_summary(payload, records, category_counts)
        message = build_completion_message(category_counts)

        set_job_state(
            job_id,
            status="completed",
            message=message,
            progress_percent=100,
            results=[format_result(item) for item in visible_results],
            summary=summary,
        )
    except (BoletinAPIError, ValueError, OSError) as exc:
        set_job_state(
            job_id,
            status="error",
            message=f"Error: {exc}",
            progress_percent=100,
        )


def _should_include_item(
    categoria: str,
    include_no_relevante: bool,
    include_descartadas: bool,
) -> bool:
    if categoria == NO_RELEVANTE:
        return include_no_relevante
    if categoria == DESCARTADA_FILTRO_ESTRUCTURAL:
        return include_descartadas
    return True


def build_summary(
    payload: dict[str, Any],
    records: list[dict[str, Any]],
    category_counts: Counter[str],
) -> dict[str, Any]:
    boletin = payload.get("boletin") if isinstance(payload.get("boletin"), dict) else {}
    first_record = records[0] if records else {}
    return {
        "numero_boletin": boletin.get("numero") or boletin.get("numero2") or first_record.get("numero_boletin") or "",
        "fecha_publicacion": boletin.get("fecha_publicacion") or first_record.get("fecha_publicacion") or "",
        "total_normas": len(records),
        "relevantes": category_counts.get(RELEVANTE, 0),
        "revision_manual": category_counts.get(REVISION_MANUAL, 0),
        "no_relevantes": category_counts.get(NO_RELEVANTE, 0),
        "descartadas": category_counts.get(DESCARTADA_FILTRO_ESTRUCTURAL, 0),
    }


def build_completion_message(category_counts: Counter[str]) -> str:
    relevantes = category_counts.get(RELEVANTE, 0)
    revision = category_counts.get(REVISION_MANUAL, 0)
    if relevantes or revision:
        return f"Analisis finalizado: {relevantes} relevantes y {revision} para revision manual."
    return "Analisis finalizado: no se detecto normativa relevante."


def format_result(item: dict[str, Any]) -> dict[str, Any]:
    anexos = item.get("anexos") if isinstance(item.get("anexos"), list) else []
    return {
        "categoria_salida": item.get("categoria_salida", ""),
        "categoria_label": category_label(str(item.get("categoria_salida", ""))),
        "nombre": item.get("nombre") or "",
        "poder": item.get("poder") or "",
        "tipo_norma": item.get("tipo_norma") or "",
        "organismo": item.get("organismo") or "",
        "sumario": item.get("sumario") or "",
        "motivo_deteccion": item.get("motivo_deteccion") or [],
        "motivo_label": " | ".join(item.get("motivo_deteccion") or []),
        "url_norma": item.get("url_norma") or "",
        "numero_boletin": item.get("numero_boletin") or "",
        "fecha_publicacion": item.get("fecha_publicacion") or "",
        "anexos": [
            {
                "nombre_anexo": anexo.get("nombre_anexo") or "Anexo",
                "url": anexo.get("url") or "",
            }
            for anexo in anexos
            if isinstance(anexo, dict) and anexo.get("url")
        ],
    }


def category_label(categoria: str) -> str:
    labels = {
        RELEVANTE: "Relevante",
        REVISION_MANUAL: "Revision manual",
        NO_RELEVANTE: "No relevante",
        DESCARTADA_FILTRO_ESTRUCTURAL: "Descartada por filtro estructural",
    }
    return labels.get(categoria, categoria)


def get_config_summary() -> dict[str, Any]:
    config = load_config()
    return {
        "keywords": len(config.keywords),
        "keywords_condicionales": len(config.keywords_requieren_accion_normativa),
        "normas_curadas": len(config.normas_curadas),
        "organismos_prioridad": len(config.organismos_prioridad),
        "poderes_incluidos": _entry_names(config.poderes_incluidos),
        "tipos_norma_incluidos": _entry_names(config.tipos_norma_incluidos),
    }


def _entry_names(entries: tuple[Any, ...]) -> list[str]:
    return [entry.original for entry in entries]


def load_raw_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def get_config_editor_values() -> dict[str, str]:
    raw_config = load_raw_config()
    return {
        field_name: "\n".join(str(value) for value in sorted_config_values(field_name, raw_config.get(field_name, [])))
        for field_name in EDITABLE_CONFIG_FIELDS
    }


def save_config_editor_values(form_data: dict[str, str]) -> dict[str, int]:
    raw_config = load_raw_config()

    updated_values = {
        "KEYWORDS": sorted_config_values(
            "KEYWORDS",
            parse_textarea_list(form_data.get("KEYWORDS", ""), "KEYWORDS"),
        ),
        "LISTA_NORMAS_CURADAS": parse_textarea_list(
            form_data.get("LISTA_NORMAS_CURADAS", ""),
            "LISTA_NORMAS_CURADAS",
        ),
        "LISTA_ORGANISMOS_PRIORIDAD": sorted_config_values(
            "LISTA_ORGANISMOS_PRIORIDAD",
            parse_textarea_list(
                form_data.get("LISTA_ORGANISMOS_PRIORIDAD", ""),
                "LISTA_ORGANISMOS_PRIORIDAD",
            ),
        ),
    }
    validate_regex_patterns(updated_values["LISTA_NORMAS_CURADAS"])

    raw_config.update(updated_values)
    backup_config_file()

    tmp_path = CONFIG_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(raw_config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(CONFIG_PATH)

    # Fuerza validacion integral con el mismo cargador usado por el detector.
    load_config(CONFIG_PATH)
    return {field_name: len(values) for field_name, values in updated_values.items()}


def parse_textarea_list(raw_text: str, field_name: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for line in raw_text.splitlines():
        value = line.strip()
        if not value or value in seen:
            continue
        values.append(value)
        seen.add(value)

    if not values:
        raise ValueError(f"{field_name} no puede quedar vacio.")
    return values


def sorted_config_values(field_name: str, values: list[str]) -> list[str]:
    if field_name not in {"KEYWORDS", "LISTA_ORGANISMOS_PRIORIDAD"}:
        return values
    return sorted((str(value) for value in values), key=lambda value: (normalize_text(value), value))


def validate_regex_patterns(patterns: list[str]) -> None:
    for pattern in patterns:
        try:
            re.compile(pattern, flags=re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"Regex invalida en LISTA_NORMAS_CURADAS: {pattern} ({exc})") from exc


def backup_config_file() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = CONFIG_PATH.with_name(f"config_keywords.backup_{timestamp}.json")
    backup_path.write_text(CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8")


@app.get("/")
def index():
    message = ""
    message_kind = "info"
    try:
        config_summary = get_config_summary()
        config_editor_values = get_config_editor_values()
    except (ValueError, OSError) as exc:
        config_summary = {}
        config_editor_values = {}
        message = f"No se pudo cargar config/config_keywords.json: {exc}"
        message_kind = "error"

    return render_template(
        "index.html",
        config_summary=config_summary,
        config_editor_values=config_editor_values,
        message=message,
        message_kind=message_kind,
        default_parametro="0",
    )


@app.post("/api/analyze")
def api_analyze():
    parametro = (request.form.get("parametro") or "0").strip() or "0"
    include_no_relevante = request.form.get("include_no_relevante") == "on"
    include_descartadas = request.form.get("include_descartadas") == "on"
    job_id = create_analysis_job(parametro, include_no_relevante, include_descartadas)
    return jsonify({"job_id": job_id})


@app.get("/api/analyze/<job_id>")
def api_analyze_status(job_id: str):
    with ANALYSIS_JOBS_LOCK:
        job = ANALYSIS_JOBS.get(job_id)

    if not job:
        return jsonify({"status": "error", "message": "Analisis no encontrado."}), 404

    return jsonify(job)


@app.post("/api/config")
def api_save_config():
    try:
        counts = save_config_editor_values(dict(request.form))
        return jsonify(
            {
                "status": "ok",
                "message": "Configuracion actualizada. Se genero una copia de respaldo.",
                "counts": counts,
            }
        )
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


def open_browser(port: int) -> None:
    webbrowser.open_new(f"http://127.0.0.1:{port}")


def main() -> None:
    port = int(os.getenv("BOCABA_DESKTOP_PORT", "7862"))
    if os.getenv("BOCABA_NO_BROWSER") != "1":
        threading.Timer(1.0, open_browser, args=[port]).start()
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
