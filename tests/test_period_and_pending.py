"""Pruebas del aviso de pendientes al cerrar un boletin y de los indicadores por periodo.

Todas las pruebas usan un directorio temporal: nunca tocan data/seguimiento.
"""

from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

import desktop_app.app as desktop_module
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
    calculate_period_indicators,
    load_week,
    update_bulletin_review,
    update_norm_review,
    upsert_analysis,
)


def make_record(identifier, category, tipo="Resolución"):
    return {
        "id_norma": identifier,
        "id_sdin": None,
        "poder": "Poder Ejecutivo",
        "tipo_norma": tipo,
        "organismo": "Organismo de prueba",
        "nombre": f"Norma {identifier}",
        "sumario": "Sumario de prueba",
        "url_norma": "",
        "motivo_deteccion": [],
        "categoria_salida": category,
    }


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.data_dir = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def add_bulletin(self, number, publication_date, records):
        return upsert_analysis(
            self.data_dir,
            {"numero_boletin": number, "fecha_publicacion": publication_date},
            records,
            datetime(2026, 7, 13, 9, 0, 0),
        )

    def decide(self, state, identifier, decision, observation=""):
        update_norm_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            f"id_norma:{identifier}",
            decision,
            observation,
        )


class PendingWarningTests(StoreTestCase):
    def test_complete_with_pending_alert_is_not_saved_and_lists_pending(self):
        state = self.add_bulletin(
            7400,
            "13/07/2026",
            [make_record(1, RELEVANTE), make_record(2, REVISION_MANUAL), make_record(3, NO_RELEVANTE)],
        )
        self.decide(state, 1, RELEVANTE_CONFIRMADA)

        result = update_bulletin_review(self.data_dir, state["semana"], state["boletin_clave"], CONTROL_COMPLETO)

        self.assertFalse(result["guardado"])
        self.assertEqual([item["clave"] for item in result["pendientes"]], ["id_norma:2"])
        stored = load_week(self.data_dir, state["semana"])["boletines"][state["boletin_clave"]]
        self.assertEqual(stored["control_complementario"], "PENDIENTE")

    def test_hidden_categories_without_decision_do_not_trigger_warning(self):
        state = self.add_bulletin(
            7400,
            "13/07/2026",
            [make_record(1, NO_RELEVANTE), make_record(2, DESCARTADA_FILTRO_ESTRUCTURAL)],
        )

        result = update_bulletin_review(self.data_dir, state["semana"], state["boletin_clave"], CONTROL_COMPLETO)

        self.assertTrue(result["guardado"])
        self.assertEqual(result["pendientes"], [])

    def test_save_anyway_stores_complete_control(self):
        state = self.add_bulletin(7400, "13/07/2026", [make_record(1, REVISION_MANUAL)])

        result = update_bulletin_review(
            self.data_dir,
            state["semana"],
            state["boletin_clave"],
            CONTROL_COMPLETO,
            confirm_pending=True,
        )

        self.assertTrue(result["guardado"])
        stored = load_week(self.data_dir, state["semana"])["boletines"][state["boletin_clave"]]
        self.assertEqual(stored["control_complementario"], CONTROL_COMPLETO)

    def test_partial_control_is_saved_without_warning(self):
        state = self.add_bulletin(7400, "13/07/2026", [make_record(1, RELEVANTE)])

        result = update_bulletin_review(self.data_dir, state["semana"], state["boletin_clave"], CONTROL_PARCIAL)

        self.assertTrue(result["guardado"])


class PeriodIndicatorTests(StoreTestCase):
    def test_norm_repeated_in_two_weeks_is_counted_once(self):
        # Viernes 17/07 (W29) y lunes 20/07 (W30) publican la misma norma 50.
        self.add_bulletin(7410, "17/07/2026", [make_record(50, DESCARTADA_FILTRO_ESTRUCTURAL, "Llamado a Concurso")])
        self.add_bulletin(7411, "20/07/2026", [make_record(50, DESCARTADA_FILTRO_ESTRUCTURAL, "Llamado a Concurso")])

        indicators = calculate_period_indicators(self.data_dir, date(2026, 7, 13), date(2026, 7, 26))

        self.assertEqual(indicators["normas_procesadas"], 1)
        self.assertEqual(indicators["descartadas"], 1)
        self.assertEqual(indicators["cobertura"]["boletines"], 2)
        self.assertEqual(indicators["dias_uso"], 2)

    def test_range_cutting_a_week_includes_only_bulletins_inside(self):
        self.add_bulletin(7406, "13/07/2026", [make_record(1, RELEVANTE)])
        self.add_bulletin(7407, "14/07/2026", [make_record(2, RELEVANTE)])
        self.add_bulletin(7408, "15/07/2026", [make_record(3, RELEVANTE)])

        indicators = calculate_period_indicators(self.data_dir, date(2026, 7, 14), date(2026, 7, 14))

        self.assertEqual(indicators["normas_procesadas"], 1)
        self.assertEqual([row["numero_boletin"] for row in indicators["boletines"]], ["7407"])

    def test_percentages_use_period_totals_not_weekly_average(self):
        # Semana 1: 1 alerta, confirmada (100 %). Semana 2: 3 alertas, 1 confirmada (33,3 %).
        # Promedio semanal: 66,7 %. Formula sobre el periodo: 2 de 4 = 50 %.
        week_one = self.add_bulletin(7406, "13/07/2026", [make_record(1, RELEVANTE)])
        week_two = self.add_bulletin(
            7411,
            "20/07/2026",
            [make_record(2, RELEVANTE), make_record(3, RELEVANTE), make_record(4, RELEVANTE)],
        )
        self.decide(week_one, 1, RELEVANTE_CONFIRMADA)
        self.decide(week_two, 2, RELEVANTE_CONFIRMADA)
        self.decide(week_two, 3, NO_RELEVANTE_CONFIRMADA)
        self.decide(week_two, 4, NO_RELEVANTE_CONFIRMADA)

        indicators = calculate_period_indicators(self.data_dir, date(2026, 7, 13), date(2026, 7, 26))

        self.assertEqual(indicators["precision_automatica"], 50.0)
        self.assertEqual(indicators["bases_desempeno"]["alertas_automaticas_validadas"], 4)

    def test_empty_period_reports_no_records_instead_of_zero(self):
        self.add_bulletin(7406, "13/07/2026", [make_record(1, RELEVANTE)])

        indicators = calculate_period_indicators(self.data_dir, date(2026, 8, 1), date(2026, 8, 31))

        self.assertTrue(indicators["cobertura"]["sin_registros"])
        self.assertEqual(indicators["precision_automatica"], "N/D")
        self.assertIn("No hay registros posteriores al 13/07/2026.", indicators["cobertura"]["avisos"])

    def test_range_outside_available_data_is_warned(self):
        self.add_bulletin(7406, "13/07/2026", [make_record(1, RELEVANTE)])

        indicators = calculate_period_indicators(self.data_dir, date(2026, 7, 1), date(2026, 7, 13))

        self.assertFalse(indicators["cobertura"]["sin_registros"])
        self.assertEqual(indicators["cobertura"]["avisos"], ["No hay registros anteriores al 13/07/2026."])

    def test_inverted_range_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_period_indicators(self.data_dir, date(2026, 7, 20), date(2026, 7, 13))


class ApiTests(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.patcher = patch.object(desktop_module, "REVIEW_DATA_DIR", self.data_dir)
        self.patcher.start()
        self.client = desktop_module.app.test_client()

    def tearDown(self):
        self.patcher.stop()
        super().tearDown()

    def test_bulletin_endpoint_returns_pending_then_saves_when_confirmed(self):
        state = self.add_bulletin(7400, "13/07/2026", [make_record(1, REVISION_MANUAL)])
        body = {
            "semana": state["semana"],
            "boletin_clave": state["boletin_clave"],
            "control_complementario": CONTROL_COMPLETO,
            "observaciones": "",
        }

        first = self.client.post("/api/review/boletin", json=body).get_json()
        second = self.client.post("/api/review/boletin", json={**body, "confirmar_pendientes": True}).get_json()

        self.assertEqual(first["status"], "pendientes")
        self.assertEqual(first["pendientes"][0]["nombre"], "Norma 1")
        self.assertEqual(second["status"], "ok")
        self.assertEqual(second["control_complementario"], CONTROL_COMPLETO)

    def test_period_endpoint_and_data_range(self):
        self.add_bulletin(7406, "13/07/2026", [make_record(1, RELEVANTE)])

        weeks = self.client.get("/api/indicators/weeks").get_json()
        period = self.client.get("/api/indicators?desde=2026-07-13&hasta=2026-07-19")

        self.assertEqual(weeks["rango_datos"], {"desde": "2026-07-13", "hasta": "2026-07-13"})
        self.assertEqual(period.status_code, 200)
        self.assertEqual(period.get_json()["normas_procesadas"], 1)

    def test_period_endpoint_requires_both_dates(self):
        response = self.client.get("/api/indicators?desde=2026-07-13")

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
