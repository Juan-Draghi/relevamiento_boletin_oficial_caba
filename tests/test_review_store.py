import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bo_detector.classifier import (
    DESCARTADA_FILTRO_ESTRUCTURAL,
    NO_RELEVANTE,
    RELEVANTE,
    REVISION_MANUAL,
)
from bo_detector.review_store import (
    CONTROL_COMPLETO,
    CONTROL_PARCIAL,
    NO_RELEVANTE_CONFIRMADA,
    RELEVANTE_CONFIRMADA,
    calculate_week_indicators,
    load_week,
    normalize_publication_date,
    record_key,
    update_bulletin_review,
    update_norm_review,
    upsert_analysis,
    week_key_for_date,
)


class ReviewStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.data_dir = Path(self.temporary_directory.name)
        self.summary = {
            "numero_boletin": 7400,
            "fecha_publicacion": "13/07/2026",
        }

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_publication_date_uses_monday_to_sunday_iso_week(self):
        publication_date = normalize_publication_date("13/07/2026")

        self.assertEqual(week_key_for_date(publication_date), "2026-W29")

    def test_repeated_analysis_and_duplicate_records_are_not_counted_twice(self):
        records = [
            self._record(1, RELEVANTE),
            self._record(1, RELEVANTE),
            self._record(2, REVISION_MANUAL),
        ]

        first = upsert_analysis(self.data_dir, self.summary, records, self._now(9))
        second = upsert_analysis(self.data_dir, self.summary, records, self._now(10))
        document = load_week(self.data_dir, "2026-W29")
        indicators = calculate_week_indicators(document)

        self.assertEqual(first["boletin_clave"], second["boletin_clave"])
        self.assertEqual(indicators["normas_procesadas"], 2)
        self.assertEqual(indicators["relevantes"], 1)
        self.assertEqual(indicators["revision_manual"], 1)
        self.assertEqual(indicators["dias_uso"], 1)

    def test_manual_relevant_from_review_is_not_false_negative(self):
        state = upsert_analysis(
            self.data_dir,
            self.summary,
            [self._record(10, REVISION_MANUAL)],
            self._now(9),
        )
        update_norm_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            "id_norma:10",
            RELEVANTE_CONFIRMADA,
            now=self._now(10),
        )
        update_bulletin_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            CONTROL_COMPLETO,
        )

        indicators = calculate_week_indicators(load_week(self.data_dir, state["semana"]))

        self.assertEqual(indicators["relevantes_confirmadas_total"], 1)
        self.assertEqual(indicators["relevantes_desde_revision_manual"], 1)
        self.assertEqual(indicators["falsos_negativos"], 0)

    def test_false_negative_requires_observation_and_is_derived(self):
        state = upsert_analysis(
            self.data_dir,
            self.summary,
            [self._record(20, NO_RELEVANTE)],
            self._now(9),
        )

        with self.assertRaisesRegex(ValueError, "observacion breve"):
            update_norm_review(
                self.data_dir,
                state["semana"],
                state["boletin_clave"],
                "id_norma:20",
                RELEVANTE_CONFIRMADA,
            )

        result = update_norm_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            "id_norma:20",
            RELEVANTE_CONFIRMADA,
            "Modifica requisitos constructivos.",
            self._now(10),
        )
        indicators = calculate_week_indicators(load_week(self.data_dir, state["semana"]))

        self.assertTrue(result["es_falso_negativo"])
        self.assertEqual(indicators["falsos_negativos"], 1)

    def test_zero_false_negatives_requires_complete_control(self):
        state = upsert_analysis(
            self.data_dir,
            self.summary,
            [self._record(30, NO_RELEVANTE)],
            self._now(9),
        )

        pending = calculate_week_indicators(load_week(self.data_dir, state["semana"]))
        update_bulletin_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            CONTROL_PARCIAL,
        )
        partial = calculate_week_indicators(load_week(self.data_dir, state["semana"]))
        update_bulletin_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            CONTROL_COMPLETO,
        )
        complete = calculate_week_indicators(load_week(self.data_dir, state["semana"]))

        self.assertEqual(pending["falsos_negativos"], "N/D")
        self.assertEqual(partial["falsos_negativos"], "N/D")
        self.assertEqual(complete["falsos_negativos"], 0)

    def test_no_activity_uses_no_utilizado(self):
        indicators = calculate_week_indicators(load_week(self.data_dir, "2026-W28"))

        self.assertEqual(indicators["dias_uso"], 0)
        self.assertEqual(indicators["normas_procesadas"], 0)
        self.assertEqual(indicators["control_complementario"], "No utilizado")
        self.assertEqual(indicators["falsos_negativos"], "N/D")
        self.assertEqual(indicators["cobertura_validacion"], "No utilizado")
        self.assertEqual(indicators["precision_automatica"], "N/D")

    def test_original_category_and_review_survive_reprocessing(self):
        state = upsert_analysis(
            self.data_dir,
            self.summary,
            [self._record(40, NO_RELEVANTE)],
            self._now(9),
        )
        update_norm_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            "id_norma:40",
            RELEVANTE_CONFIRMADA,
            "Caso confirmado durante la revision.",
            self._now(10),
        )

        upsert_analysis(
            self.data_dir,
            self.summary,
            [self._record(40, RELEVANTE)],
            self._now(11),
        )
        document = load_week(self.data_dir, state["semana"])
        norm = document["boletines"][state["boletin_clave"]]["normas"]["id_norma:40"]

        self.assertEqual(norm["categoria_automatica_original"], NO_RELEVANTE)
        self.assertEqual(norm["decision_manual"], RELEVANTE_CONFIRMADA)

    def test_non_relevant_confirmation_can_be_recorded(self):
        state = upsert_analysis(
            self.data_dir,
            self.summary,
            [self._record(50, RELEVANTE)],
            self._now(9),
        )
        result = update_norm_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            "id_norma:50",
            NO_RELEVANTE_CONFIRMADA,
            now=self._now(10),
        )

        self.assertEqual(result["decision_manual"], NO_RELEVANTE_CONFIRMADA)
        self.assertFalse(result["es_falso_negativo"])

    def test_performance_indicators_use_validated_denominators(self):
        state = upsert_analysis(
            self.data_dir,
            self.summary,
            [
                self._record(70, RELEVANTE),
                self._record(71, RELEVANTE),
                self._record(72, REVISION_MANUAL),
                self._record(73, REVISION_MANUAL),
                self._record(74, NO_RELEVANTE),
                self._record(75, DESCARTADA_FILTRO_ESTRUCTURAL),
            ],
            self._now(9),
        )
        decisions = {
            70: RELEVANTE_CONFIRMADA,
            71: NO_RELEVANTE_CONFIRMADA,
            72: RELEVANTE_CONFIRMADA,
            73: NO_RELEVANTE_CONFIRMADA,
            74: NO_RELEVANTE_CONFIRMADA,
        }
        for identifier, decision in decisions.items():
            update_norm_review(
                self.data_dir,
                state["semana"],
                state["boletin_clave"],
                f"id_norma:{identifier}",
                decision,
                now=self._now(10),
            )

        indicators = calculate_week_indicators(load_week(self.data_dir, state["semana"]))

        self.assertEqual(indicators["cobertura_validacion"], 83.3)
        self.assertEqual(indicators["precision_automatica"], 50.0)
        self.assertEqual(indicators["tasa_falsos_positivos"], 50.0)
        self.assertEqual(indicators["tasa_revision_manual"], 33.3)
        self.assertEqual(indicators["rendimiento_revision_manual"], 50.0)
        self.assertEqual(indicators["reduccion_lectura"], 33.3)
        self.assertEqual(
            indicators["bases_desempeno"],
            {
                "normas_validadas": 5,
                "alertas_automaticas_validadas": 2,
                "casos_revision_manual_validados": 2,
            },
        )
    def test_week_json_is_utf8_and_human_readable(self):
        upsert_analysis(
            self.data_dir,
            self.summary,
            [self._record(60, DESCARTADA_FILTRO_ESTRUCTURAL, "Código Urbanístico")],
            self._now(9),
        )

        path = self.data_dir / "2026-W29.json"
        parsed = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(parsed["schema_version"], 1)
        self.assertIn("Código Urbanístico", path.read_text(encoding="utf-8"))

    def _record(self, identifier, category, summary="Sumario de prueba"):
        return {
            "id_norma": identifier,
            "id_sdin": None,
            "numero_boletin": 7400,
            "fecha_publicacion": "13/07/2026",
            "poder": "Poder Ejecutivo",
            "tipo_norma": "Resolución",
            "organismo": "Organismo de prueba",
            "nombre": f"Resolución {identifier}",
            "sumario": summary,
            "url_norma": f"https://example.test/{identifier}",
            "motivo_deteccion": [],
            "categoria_salida": category,
        }

    @staticmethod
    def _now(hour):
        return datetime(2026, 7, 13, hour, 0, 0)


class RecordKeyTests(unittest.TestCase):
    def test_record_key_prefers_identifiers(self):
        self.assertEqual(record_key({"id_norma": 123, "id_sdin": 456}), "id_norma:123")
        self.assertEqual(record_key({"id_sdin": 456}), "id_sdin:456")

    def test_record_key_has_stable_fallback(self):
        record = {"nombre": "Resolución 1", "sumario": "Aprueba un régimen"}

        self.assertEqual(record_key(record), record_key(dict(record)))


if __name__ == "__main__":
    unittest.main()
