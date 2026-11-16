"""Revision de estrategias del detector del Boletin Oficial CABA.

SOLO LECTURA: no modifica la configuracion ni los JSON semanales.

Uso (desde la carpeta del proyecto):

    Informe por termino de todo el historico:
        python scripts/revisar_estrategias.py terminos

    Informe por termino de un periodo:
        python scripts/revisar_estrategias.py terminos --desde 2026-07-13 --hasta 2026-09-30

    Comparar la configuracion vigente con una propuesta:
        python scripts/revisar_estrategias.py comparar --propuesta data/informes_estrategias/propuesta.json

Formato de la propuesta (JSON UTF-8):
    {
      "descripcion": "Retirar 'habilitación' por falsos positivos",
      "cambios": [
        {"lista": "KEYWORDS", "operacion": "eliminar", "valor": "habilitación"},
        {"lista": "KEYWORDS", "operacion": "agregar", "valor": "nuevo término"},
        {"lista": "KEYWORDS", "operacion": "reemplazar", "valor": "viejo", "nuevo": "nuevo"}
      ]
    }

Salidas: un informe Markdown y un CSV con el detalle, en
data/informes_estrategias/ (carpeta excluida de Git porque contiene sumarios
reales).
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from bo_detector.config import DEFAULT_CONFIG_PATH, config_from_dict  # noqa: E402
from bo_detector.review_store import data_date_range, normalize_publication_date  # noqa: E402
from bo_detector.strategy_review import (  # noqa: E402
    EVIDENCIA_CUMPLE_MINIMO,
    EVIDENCIA_EN_OBSERVACION,
    MIN_EVIDENCE_CASES,
    PeriodData,
    apply_proposal,
    compare_configs,
    load_period_norms,
    term_report,
)

# --- Configuracion editable --------------------------------------------------
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "seguimiento"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "informes_estrategias"
# -----------------------------------------------------------------------------

REFERENCE_NOTE = (
    "Referencia profesional: **relevante** y **no relevante** = decisión registrada; "
    "**no relevante (lectura)** = norma oculta sin marca en un boletín con control completo; "
    "**sin información** = sin decisión ni control completo (no cuenta como relevante ni como irrelevante)."
)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        data_dir = Path(args.datos).resolve()
        output_dir = Path(args.salida).resolve()
        if output_dir == data_dir or data_dir in output_dir.parents:
            raise ValueError("La carpeta de salida no puede estar dentro de la carpeta de registros semanales.")
        start, end = _resolve_period(data_dir, args.desde, args.hasta)
        raw_config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        period = load_period_norms(data_dir, start, end)
        if not period.normas:
            print(f"Sin registros entre {start.isoformat()} y {end.isoformat()}.")
            return 1

        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.modo == "terminos":
            rows = term_report(period, config_from_dict(raw_config))
            md_path = output_dir / f"{stamp}_terminos.md"
            csv_path = output_dir / f"{stamp}_terminos.csv"
            md_path.write_text(_terms_markdown(period, rows), encoding="utf-8")
            _write_terms_csv(csv_path, rows)
        else:
            proposal = json.loads(Path(args.propuesta).read_text(encoding="utf-8"))
            proposed_raw = apply_proposal(raw_config, proposal)
            result = compare_configs(period, raw_config, proposed_raw)
            md_path = output_dir / f"{stamp}_comparacion.md"
            csv_path = output_dir / f"{stamp}_comparacion.csv"
            md_path.write_text(_comparison_markdown(period, proposal, result), encoding="utf-8")
            _write_rows_csv(csv_path, result["detalle"])
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Informe: {md_path}")
    print(f"Detalle: {csv_path}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Revision de estrategias del detector (solo lectura).")
    parser.add_argument("modo", choices=["terminos", "comparar"])
    parser.add_argument("--desde", help="Fecha inicial AAAA-MM-DD (por defecto, primer registro).")
    parser.add_argument("--hasta", help="Fecha final AAAA-MM-DD (por defecto, ultimo registro).")
    parser.add_argument("--propuesta", help="Archivo JSON con los cambios propuestos (modo comparar).")
    parser.add_argument("--datos", default=str(DEFAULT_DATA_DIR), help="Carpeta de los JSON semanales.")
    parser.add_argument("--salida", default=str(DEFAULT_OUTPUT_DIR), help="Carpeta de los informes.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuracion vigente.")
    args = parser.parse_args(argv)
    if args.modo == "comparar" and not args.propuesta:
        parser.error("el modo comparar requiere --propuesta")
    return args


def _resolve_period(data_dir: Path, start_text: str | None, end_text: str | None) -> tuple[date, date]:
    available = data_date_range(data_dir)
    if not available and not (start_text and end_text):
        raise ValueError("No hay registros semanales para definir el periodo.")
    start = normalize_publication_date(start_text or available["desde"])
    end = normalize_publication_date(end_text or available["hasta"])
    return start, end


# --- Informe por termino -----------------------------------------------------


def _terms_markdown(period: PeriodData, rows: list[dict]) -> str:
    refs = period.reference_counts()
    with_matches = [row for row in rows if row["coincidencias"]]
    candidates = sorted(
        (row for row in with_matches if row["estado_evidencia"] == EVIDENCIA_CUMPLE_MINIMO),
        key=lambda row: (-row["evaluables"], row["valor"]),
    )
    observation = sorted(
        (row for row in with_matches if row["estado_evidencia"] == EVIDENCIA_EN_OBSERVACION),
        key=lambda row: (-row["evaluables"], row["valor"]),
    )
    with_relevant = sorted(
        (row for row in with_matches if row["relevantes"]),
        key=lambda row: (-row["relevantes"], row["valor"]),
    )
    no_base = [row for row in with_matches if not row["evaluables"]]

    lines = [
        "# Informe por término del detector",
        "",
        f"- Período: {period.desde} a {period.hasta}",
        f"- Boletines: {period.boletines}",
        f"- Normas distintas: {len(period.normas)}",
        f"- Relevantes: {refs['RELEVANTE']} · No relevantes (decisión): {refs['NO_RELEVANTE']} · "
        f"No relevantes (lectura): {refs['NO_RELEVANTE_LECTURA']} · Sin información: {refs['SIN_INFORMACION']}",
        f"- Términos con coincidencias: {len(with_matches)} de {len(rows)}",
        "",
        REFERENCE_NOTE,
        "",
        "Las coincidencias se cuentan como las usa el clasificador: las keywords condicionales sólo con "
        "contexto de acción normativa y los organismos sólo con verbo de acción o referencia normativa. "
        "**Decide** = la norma deja de estar en la lista principal si se retira el término; "
        "**sigue** = la norma seguiría seleccionada por otra regla.",
        "",
        f"Criterio de evidencia mínima (docs/seguimiento/criterio_evidencia_keywords.md): proponer retirar o "
        f"restringir un término sólo con al menos {MIN_EVIDENCE_CASES} casos evaluados y ninguno relevante. "
        "**Tasa máx. (3/n)** = con 0 relevantes en n casos evaluados, la tasa real de relevantes no supera 3/n "
        "con 95 % de confianza. Los términos estacionales requieren además un ciclo anual completo.",
        "",
        "## Candidatos a revisión",
        "",
        f"Cumplen el mínimo de evidencia: {MIN_EVIDENCE_CASES} o más casos evaluados y ninguno relevante. "
        "Es una señal para revisar, no una orden de retiro.",
        "",
    ]
    lines += _terms_table(candidates) if candidates else ["Ninguno en el período.", ""]
    lines += [
        "## En observación",
        "",
        f"Ningún caso relevante, pero menos de {MIN_EVIDENCE_CASES} casos evaluados: no proponer su retiro todavía.",
        "",
    ]
    lines += _terms_table(observation) if observation else ["Ninguno en el período.", ""]
    lines += ["## Términos con relevantes confirmadas", ""]
    lines += _terms_table(with_relevant) if with_relevant else ["Ninguno en el período.", ""]
    lines += ["## Términos con coincidencias sin base de evaluación", ""]
    lines += _terms_table(no_base) if no_base else ["Ninguno en el período.", ""]
    lines += [
        "El detalle completo de todos los términos está en el CSV del mismo informe.",
        "",
    ]
    return "\n".join(lines)


def _terms_table(rows: list[dict]) -> list[str]:
    lines = [
        "| Término | Lista | Coinc. | Relev. | No rel. (decisión) | No rel. (lectura) | Sin inf. | % no relevante (base) | Tasa máx. (3/n) | Evidencia | Decide / sigue | Ejemplos |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        percent = row["porcentaje_no_relevante"]
        percent_text = f"{_percent(percent)} ({row['evaluables']})" if isinstance(percent, float) else f"{percent}"
        examples = "; ".join(
            f"{item['nombre']} (BO {item['numero_boletin']})" for item in row["ejemplos"][:3]
        )
        value = row["valor"] + (" [condicional]" if row["condicional"] else "")
        lines.append(
            f"| {_md(value)} | {row['lista']} | {row['coincidencias']} | {row['relevantes']} | "
            f"{row['no_relevantes_decision']} | {row['no_relevantes_lectura']} | {row['sin_informacion']} | "
            f"{percent_text} | {_percent(row['tasa_maxima_relevantes']) if row['tasa_maxima_relevantes'] is not None else '—'} | "
            f"{row['estado_evidencia']} | {row['decide_seleccion']} / {row['sigue_por_otra_regla']} | {_md(examples)} |"
        )
    lines.append("")
    return lines


def _write_terms_csv(path: Path, rows: list[dict]) -> None:
    flat = []
    for row in rows:
        item = {key: value for key, value in row.items() if key != "ejemplos"}
        item["ejemplos"] = " | ".join(
            f"{example['nombre']} (BO {example['numero_boletin']}, {example['referencia']})"
            for example in row["ejemplos"]
        )
        flat.append(item)
    _write_rows_csv(path, flat)


# --- Comparacion -------------------------------------------------------------

EFFECT_TITLES = [
    ("relevantes_recuperadas", "Relevantes recuperadas", "relevantes_recuperadas", "relevantes_no_seleccionadas_vigente"),
    ("relevantes_perdidas", "Relevantes perdidas", "relevantes_perdidas", "relevantes_seleccionadas_vigente"),
    ("irrelevantes_evitadas_decision", "Irrelevantes evitadas (decisión)", None, None),
    ("irrelevantes_evitadas_lectura", "Irrelevantes evitadas (lectura completa)", None, None),
    ("irrelevantes_anadidas_decision", "Irrelevantes añadidas (decisión)", None, None),
    ("irrelevantes_anadidas_lectura", "Irrelevantes añadidas (lectura completa)", None, None),
    ("sin_informacion_anadidas", "Sin información que entran a la selección", None, None),
    ("sin_informacion_evitadas", "Sin información que salen de la selección", None, None),
    ("cambios_relevante_revision_manual", "Pasan entre RELEVANTE y REVISION_MANUAL", None, None),
]


def _comparison_markdown(period: PeriodData, proposal: dict, result: dict) -> str:
    summary = result["resumen"]
    bases = result["bases"]
    percentages = result["porcentajes"]
    lines = [
        "# Comparación de configuración vigente y propuesta",
        "",
        f"- Período: {period.desde} a {period.hasta} · {period.boletines} boletines · {len(period.normas)} normas distintas",
        f"- Propuesta: {proposal.get('descripcion') or '(sin descripción)'}",
        "",
        "## Cambios propuestos",
        "",
    ]
    for change in proposal.get("cambios", []):
        detail = f" → `{change['nuevo']}`" if change.get("operacion") == "reemplazar" else ""
        lines.append(f"- {change.get('operacion')} en `{change.get('lista')}`: `{change.get('valor')}`{detail}")
    lines += [
        "",
        "## Efectos medidos sobre el histórico",
        "",
        REFERENCE_NOTE,
        "",
        "«Seleccionada» = RELEVANTE o REVISION_MANUAL (lista principal). Cada norma se cuenta una vez.",
        "",
        "| Efecto | Cantidad | Porcentaje (base) | Ejemplos |",
        "|---|---|---|---|",
    ]
    for key, title, percent_key, base_key in EFFECT_TITLES:
        percent_text = ""
        if percent_key:
            value = percentages[percent_key]
            percent_text = f"{_percent(value)} ({bases[base_key]})" if isinstance(value, float) else f"{value}"
        examples = "; ".join(
            f"{item['nombre']} (BO {item['numero_boletin']})" for item in result["ejemplos"][key][:3]
        )
        lines.append(f"| {title} | {summary[key]} | {percent_text} | {_md(examples)} |")

    evitadas = summary["irrelevantes_evitadas_decision"] + summary["irrelevantes_evitadas_lectura"]
    anadidas = summary["irrelevantes_anadidas_decision"] + summary["irrelevantes_anadidas_lectura"]
    lines += [
        "",
        f"- Irrelevantes evitadas en total: {evitadas} de {bases['irrelevantes_seleccionadas_vigente']} "
        f"irrelevantes que hoy se seleccionan ({_percent(percentages['irrelevantes_evitadas'])}).",
        f"- Irrelevantes añadidas en total: {anadidas} de {bases['irrelevantes_no_seleccionadas_vigente']} "
        f"irrelevantes que hoy no se seleccionan ({_percent(percentages['irrelevantes_anadidas'])}).",
        "",
    ]
    if summary["relevantes_perdidas"]:
        lines += [
            f"**Atención: la propuesta pierde {summary['relevantes_perdidas']} norma(s) relevante(s) conocida(s).** "
            "Ver el detalle en el CSV.",
            "",
        ]

    if result["siguen_por_otra_regla"]:
        lines += [
            "## Valores retirados que no eliminan la selección",
            "",
            "| Valor | Lista | Seleccionadas hoy por el valor | Siguen seleccionadas por otra regla |",
            "|---|---|---|---|",
        ]
        for item in result["siguen_por_otra_regla"]:
            lines.append(
                f"| {_md(item['valor'])} | {item['lista']} | {item['seleccionadas_por_el_valor']} | "
                f"{item['siguen_seleccionadas']} |"
            )
        lines.append("")

    lines += [
        "## Alcance",
        "",
        "Resultados medidos sobre los boletines del período con la configuración vigente y la propuesta "
        "aplicadas hoy. No garantizan el mismo efecto en boletines futuros: después de aplicar un ajuste, "
        "revisar su desempeño con el informe por término sobre los boletines posteriores.",
        "",
    ]
    return "\n".join(lines)


# --- Utilidades ---------------------------------------------------------------


def _write_rows_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["sin_resultados"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _percent(value) -> str:
    """Porcentaje con coma decimal, como en la interfaz de la aplicacion."""
    return f"{value:.1f}".replace(".", ",") + " %" if isinstance(value, float) else str(value)


def _md(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    sys.exit(main())
