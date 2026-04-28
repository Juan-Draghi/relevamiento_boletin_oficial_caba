from __future__ import annotations

from typing import Any

from .classifier import DESCARTADA_FILTRO_ESTRUCTURAL, NO_RELEVANTE, classify_norma
from .config import DetectorConfig, load_config
from .flatten import flatten_normas_payload


def classify_records(
    records: list[dict[str, Any]],
    config: DetectorConfig | None = None,
    include_no_relevante: bool = False,
    include_descartadas: bool = False,
) -> list[dict[str, Any]]:
    detector_config = config or load_config()
    output: list[dict[str, Any]] = []

    for record in records:
        result = classify_norma(record, detector_config)
        if result.categoria_salida == DESCARTADA_FILTRO_ESTRUCTURAL and not include_descartadas:
            continue
        if result.categoria_salida == NO_RELEVANTE and not include_no_relevante:
            continue

        enriched = dict(record)
        enriched["categoria_salida"] = result.categoria_salida
        enriched["motivo_deteccion"] = list(result.motivo_deteccion)
        output.append(enriched)

    return output


def classify_boletin_payload(
    payload: dict[str, Any],
    config: DetectorConfig | None = None,
    include_no_relevante: bool = False,
    include_descartadas: bool = False,
) -> list[dict[str, Any]]:
    return classify_records(
        flatten_normas_payload(payload),
        config=config,
        include_no_relevante=include_no_relevante,
        include_descartadas=include_descartadas,
    )
