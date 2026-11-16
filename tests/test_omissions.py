"""Pruebas del indicador de omisiones identificadas y de los avisos de consistencia.

Reproducen los ejemplos de aceptacion de la especificacion. Usan un
directorio temporal: nunca tocan data/seguimiento.
"""

from datetime import date, datetime
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
    calculate_period_indicators,
    update_bulletin_review,
    update_norm_review,
)
from tests.test_period_and_pending import StoreTestCase, make_record

START = date(2026, 7, 13)
END = date(2026, 7, 26)


class OmissionIndicatorTests(StoreTestCase):
    def build_spec_example(self, control):
        """15 relevantes automaticas confirmadas, 3 de revision manual y 2 omisiones."""
        records = (
            [make_record(i, RELEVANTE) for i in range(1, 16)]
            + [make_record(i, REVISION_MANUAL) for i in range(16, 19)]
            + [make_record(19, NO_RELEVANTE), make_record(20, DESCARTADA_FILTRO_ESTRUCTURAL)]
        )
        state = self.add_bulletin(7406, "13/07/2026", records)
        for identifier in range(1, 19):
            self.decide(state, identifier, RELEVANTE_CONFIRMADA)
        self.decide(state, 19, RELEVANTE_CONFIRMADA, "Omision detectada en la lectura.")
        self.decide(state, 20, RELEVANTE_CONFIRMADA, "Omision detectada en la lectura.")
        update_bulletin_review(self.data_dir, state["semana"], state["boletin_clave"], control)
        return calculate_period_indicators(self.data_dir, START, END)

    def test_spec_example_gives_two_of_twenty(self):
        indicators = self.build_spec_example(CONTROL_COMPLETO)

        self.assertEqual(indicators["omisiones_identificadas"], 2)
        self.assertEqual(indicators["relevantes_confirmadas_total"], 20)
        self.assertEqual(indicators["porcentaje_omisiones"], 10.0)
        self.assertFalse(indicators["omisiones_provisional"])

    def test_same_example_with_partial_control_is_provisional(self):
        indicators = self.build_spec_example(CONTROL_PARCIAL)

        self.assertEqual(indicators["porcentaje_omisiones"], 10.0)
        self.assertTrue(indicators["omisiones_provisional"])
        self.assertIn("Hay boletines sin control complementario completo.", indicators["motivos_provisional"])

    def test_no_confirmed_relevant_is_not_calculable(self):
        state = self.add_bulletin(7406, "13/07/2026", [make_record(1, RELEVANTE)])
        self.decide(state, 1, NO_RELEVANTE_CONFIRMADA)

        indicators = calculate_period_indicators(self.data_dir, START, END)

        self.assertEqual(indicators["porcentaje_omisiones"], "No calculable")

    def test_zero_omissions_with_pending_control_is_provisional(self):
        state = self.add_bulletin(7406, "13/07/2026", [make_record(1, RELEVANTE)])
        self.decide(state, 1, RELEVANTE_CONFIRMADA)

        indicators = calculate_period_indicators(self.data_dir, START, END)

        self.assertEqual(indicators["porcentaje_omisiones"], 0.0)
        self.assertTrue(indicators["omisiones_provisional"])

    def test_pending_alert_makes_result_provisional_even_with_complete_control(self):
        state = self.add_bulletin(
            7406,
            "13/07/2026",
            [make_record(1, RELEVANTE), make_record(2, REVISION_MANUAL)],
        )
        self.decide(state, 1, RELEVANTE_CONFIRMADA)
        update_bulletin_review(
            self.data_dir, state["semana"], state["boletin_clave"], CONTROL_COMPLETO, confirm_pending=True
        )

        indicators = calculate_period_indicators(self.data_dir, START, END)
        checks = indicators["avisos_consistencia"]

        self.assertTrue(indicators["omisiones_provisional"])
        self.assertEqual(indicators["motivos_provisional"], ["Hay alertas sin decisión profesional."])
        self.assertEqual([item["nombre"] for item in checks["pendientes"]], ["Norma 2"])
        self.assertEqual(checks["completos_con_pendientes"][0]["numero_boletin"], "7406")


class RepeatedNormDecisionTests(StoreTestCase):
    def test_omission_marked_on_second_appearance_is_counted(self):
        # El llamado 50 se publica el 13/07 y el 14/07; la omision se marca en la segunda copia.
        record = make_record(50, DESCARTADA_FILTRO_ESTRUCTURAL, "Llamado a Concurso")
        self.add_bulletin(7406, "13/07/2026", [record, make_record(1, RELEVANTE)])
        second = self.add_bulletin(7407, "14/07/2026", [record])
        self.decide(second, 50, RELEVANTE_CONFIRMADA, "Omision detectada en la lectura.")

        indicators = calculate_period_indicators(self.data_dir, START, END)

        self.assertEqual(indicators["normas_procesadas"], 2)
        self.assertEqual(indicators["omisiones_identificadas"], 1)
        self.assertEqual(indicators["relevantes_confirmadas_total"], 1)

    def test_contradictory_decisions_are_reported_and_latest_is_used(self):
        record = make_record(60, RELEVANTE)
        first = self.add_bulletin(7406, "13/07/2026", [record])
        second = self.add_bulletin(7407, "14/07/2026", [record])
        update_norm_review(
            self.data_dir, first["semana"], first["boletin_clave"], "id_norma:60",
            NO_RELEVANTE_CONFIRMADA, now=datetime(2026, 7, 13, 10, 0, 0),
        )
        update_norm_review(
            self.data_dir, second["semana"], second["boletin_clave"], "id_norma:60",
            RELEVANTE_CONFIRMADA, now=datetime(2026, 7, 14, 10, 0, 0),
        )

        indicators = calculate_period_indicators(self.data_dir, START, END)
        contradictions = indicators["avisos_consistencia"]["contradicciones"]

        self.assertEqual(len(contradictions), 1)
        self.assertEqual(contradictions[0]["nombre"], "Norma 60")
        self.assertEqual(indicators["relevantes_confirmadas_total"], 1)
        self.assertEqual(indicators["tasa_falsos_positivos"], 0.0)


if __name__ == "__main__":
    unittest.main()
