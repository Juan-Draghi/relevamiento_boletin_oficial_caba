"""Pruebas de la revision de estrategias (informe por termino y comparacion).

Usan una configuracion ficticia y registros en un directorio temporal:
nunca leen ni modifican config/config_keywords.json ni data/seguimiento.
"""

from datetime import date
import hashlib
import json
from pathlib import Path
import unittest

from bo_detector.classifier import DESCARTADA_FILTRO_ESTRUCTURAL, NO_RELEVANTE, RELEVANTE, REVISION_MANUAL
from bo_detector.config import config_from_dict
from bo_detector.review_store import (
    CONTROL_COMPLETO,
    NO_RELEVANTE_CONFIRMADA,
    RELEVANTE_CONFIRMADA,
    update_bulletin_review,
)
from bo_detector.strategy_review import (
    EVIDENCIA_APORTA_RELEVANTES,
    EVIDENCIA_CUMPLE_MINIMO,
    EVIDENCIA_EN_OBSERVACION,
    EVIDENCIA_SIN_BASE,
    REF_NO_RELEVANTE_LECTURA,
    REF_SIN_INFORMACION,
    apply_proposal,
    compare_configs,
    evidence_status,
    load_period_norms,
    term_report,
)
from scripts import revisar_estrategias
from tests.test_period_and_pending import StoreTestCase

START = date(2026, 7, 13)
END = date(2026, 7, 19)

RAW_CONFIG = {
    "PODERES_INCLUIDOS": ["Poder Ejecutivo"],
    "TIPOS_NORMA_INCLUIDOS": ["Resolución"],
    "KEYWORDS": ["habilitación", "demolición", "obra nueva"],
    "KEYWORDS_REQUIEREN_ACCION_NORMATIVA": [],
    "VERBOS_ACCION": ["\\baprueba\\b"],
    "LISTA_NORMAS_CURADAS": ["[Ll]ey 1234"],
    "LISTA_ORGANISMOS_PRIORIDAD": ["SSGOU"],
}


def record(identifier, category, sumario, organismo="Organismo de prueba"):
    return {
        "id_norma": identifier,
        "id_sdin": None,
        "poder": "Poder Ejecutivo",
        "tipo_norma": "Resolución",
        "organismo": organismo,
        "nombre": f"Resolución {identifier}",
        "sumario": sumario,
        "url_norma": "",
        "motivo_deteccion": [],
        "categoria_salida": category,
    }


def row_for(rows, value):
    return next(row for row in rows if row["valor"] == value)


class StrategyReviewTests(StoreTestCase):
    def build(self, records, decisions, complete=True):
        state = self.add_bulletin(7406, "13/07/2026", records)
        for identifier, decision in decisions.items():
            observation = "Omision detectada." if decision == RELEVANTE_CONFIRMADA else ""
            self.decide(state, identifier, decision, observation)
        if complete:
            update_bulletin_review(
                self.data_dir, state["semana"], state["boletin_clave"], CONTROL_COMPLETO, confirm_pending=True
            )
        return load_period_norms(self.data_dir, START, END)

    def test_term_with_all_evaluated_cases_not_relevant_is_candidate(self):
        period = self.build(
            [
                record(1, RELEVANTE, "Otorga habilitación a un local"),
                record(2, RELEVANTE, "Deniega habilitación de un comercio"),
                record(3, RELEVANTE, "Aprueba demolición en el barrio"),
            ],
            {1: NO_RELEVANTE_CONFIRMADA, 2: NO_RELEVANTE_CONFIRMADA, 3: RELEVANTE_CONFIRMADA},
        )

        rows = term_report(period, config_from_dict(RAW_CONFIG))
        habilitacion = row_for(rows, "habilitación")

        self.assertEqual(habilitacion["coincidencias"], 2)
        self.assertEqual(habilitacion["no_relevantes_decision"], 2)
        self.assertEqual(habilitacion["porcentaje_no_relevante"], 100.0)
        self.assertTrue(habilitacion["candidato_revision"])
        self.assertEqual(habilitacion["decide_seleccion"], 2)
        self.assertEqual(len(habilitacion["ejemplos"]), 2)
        self.assertFalse(row_for(rows, "demolición")["candidato_revision"])

    def test_evidence_status_follows_minimum_criterion(self):
        cases = [
            ((0, 0), (EVIDENCIA_SIN_BASE, None)),
            ((1, 40), (EVIDENCIA_APORTA_RELEVANTES, None)),
            ((0, 29), (EVIDENCIA_EN_OBSERVACION, 10.3)),
            ((0, 30), (EVIDENCIA_CUMPLE_MINIMO, 10.0)),
            ((0, 128), (EVIDENCIA_CUMPLE_MINIMO, 2.3)),
            ((0, 2), (EVIDENCIA_EN_OBSERVACION, 100.0)),
        ]
        for (relevant, evaluable), expected in cases:
            with self.subTest(relevant=relevant, evaluable=evaluable):
                self.assertEqual(evidence_status(relevant, evaluable), expected)

    def test_term_with_few_cases_is_in_observation(self):
        period = self.build(
            [record(1, RELEVANTE, "Otorga habilitación a un local")],
            {1: NO_RELEVANTE_CONFIRMADA},
        )

        habilitacion = row_for(term_report(period, config_from_dict(RAW_CONFIG)), "habilitación")

        self.assertEqual(habilitacion["estado_evidencia"], EVIDENCIA_EN_OBSERVACION)
        self.assertEqual(habilitacion["tasa_maxima_relevantes"], 100.0)

    def test_term_with_thirty_cases_meets_minimum(self):
        records = [record(i, RELEVANTE, f"Otorga habilitación al local {i}") for i in range(1, 31)]
        period = self.build(records, {i: NO_RELEVANTE_CONFIRMADA for i in range(1, 31)})

        habilitacion = row_for(term_report(period, config_from_dict(RAW_CONFIG)), "habilitación")

        self.assertEqual(habilitacion["evaluables"], 30)
        self.assertEqual(habilitacion["estado_evidencia"], EVIDENCIA_CUMPLE_MINIMO)
        self.assertEqual(habilitacion["tasa_maxima_relevantes"], 10.0)

    def test_term_without_decisions_has_no_base(self):
        period = self.build([record(1, RELEVANTE, "Otorga habilitación a un local")], {}, complete=False)

        habilitacion = row_for(term_report(period, config_from_dict(RAW_CONFIG)), "habilitación")

        self.assertEqual(habilitacion["sin_informacion"], 1)
        self.assertEqual(habilitacion["porcentaje_no_relevante"], "Sin base")
        self.assertFalse(habilitacion["candidato_revision"])

    def test_hidden_norm_without_mark_counts_as_read_only_with_complete_control(self):
        complete = self.build([record(1, NO_RELEVANTE, "Designa personal")], {})
        self.assertEqual(complete.normas[0].referencia, REF_NO_RELEVANTE_LECTURA)

    def test_hidden_norm_without_control_is_without_information(self):
        pending = self.build([record(1, NO_RELEVANTE, "Designa personal")], {}, complete=False)
        self.assertEqual(pending.normas[0].referencia, REF_SIN_INFORMACION)

    def test_removed_term_with_shared_match_keeps_selection_by_other_rule(self):
        # La norma 1 coincide con "habilitación" y con "demolición".
        period = self.build(
            [
                record(1, RELEVANTE, "Otorga habilitación para demolición"),
                record(2, RELEVANTE, "Otorga habilitación a un local"),
            ],
            {1: NO_RELEVANTE_CONFIRMADA, 2: NO_RELEVANTE_CONFIRMADA},
        )
        proposed = apply_proposal(
            RAW_CONFIG, {"cambios": [{"lista": "KEYWORDS", "operacion": "eliminar", "valor": "habilitación"}]}
        )

        result = compare_configs(period, RAW_CONFIG, proposed)
        shared = result["siguen_por_otra_regla"][0]

        self.assertEqual(result["resumen"]["irrelevantes_evitadas_decision"], 1)
        self.assertEqual(shared["seleccionadas_por_el_valor"], 2)
        self.assertEqual(shared["siguen_seleccionadas"], 1)

    def test_proposal_that_recovers_and_loses_shows_both_effects(self):
        period = self.build(
            [
                record(1, NO_RELEVANTE, "Modifica la Ley 9999 de edificación"),
                record(2, RELEVANTE, "Regula la obra nueva en altura"),
            ],
            {1: RELEVANTE_CONFIRMADA, 2: RELEVANTE_CONFIRMADA},
        )
        proposed = apply_proposal(
            RAW_CONFIG,
            {
                "cambios": [
                    {"lista": "LISTA_NORMAS_CURADAS", "operacion": "agregar", "valor": "[Ll]ey 9999"},
                    {"lista": "KEYWORDS", "operacion": "eliminar", "valor": "obra nueva"},
                ]
            },
        )

        result = compare_configs(period, RAW_CONFIG, proposed)

        self.assertEqual(result["resumen"]["relevantes_recuperadas"], 1)
        self.assertEqual(result["resumen"]["relevantes_perdidas"], 1)
        self.assertEqual(result["porcentajes"]["relevantes_perdidas"], 100.0)

    def test_move_from_hidden_to_manual_review_counts_as_added(self):
        period = self.build([record(1, NO_RELEVANTE, "Aprueba el procedimiento", organismo="SSGOU")], {})
        no_organism = dict(RAW_CONFIG, LISTA_ORGANISMOS_PRIORIDAD=[])
        proposed = apply_proposal(
            no_organism, {"cambios": [{"lista": "LISTA_ORGANISMOS_PRIORIDAD", "operacion": "agregar", "valor": "SSGOU"}]}
        )

        result = compare_configs(period, no_organism, proposed)

        self.assertEqual(result["resumen"]["irrelevantes_anadidas_lectura"], 1)
        self.assertEqual(result["detalle"][0]["categoria_propuesta"], REVISION_MANUAL)

    def test_current_against_current_has_no_effects(self):
        period = self.build(
            [record(1, RELEVANTE, "Otorga habilitación"), record(2, DESCARTADA_FILTRO_ESTRUCTURAL, "Licitación")],
            {1: NO_RELEVANTE_CONFIRMADA},
        )

        result = compare_configs(period, RAW_CONFIG, RAW_CONFIG)

        self.assertTrue(all(count == 0 for count in result["resumen"].values()))
        self.assertEqual(result["detalle"], [])

    def test_invalid_proposals_are_rejected(self):
        invalid = [
            {"cambios": [{"lista": "PODERES_INCLUIDOS", "operacion": "agregar", "valor": "Poder Judicial"}]},
            {"cambios": [{"lista": "KEYWORDS", "operacion": "eliminar", "valor": "inexistente"}]},
            {"cambios": [{"lista": "KEYWORDS", "operacion": "agregar", "valor": "habilitación"}]},
            {"cambios": [{"lista": "KEYWORDS_REQUIEREN_ACCION_NORMATIVA", "operacion": "agregar", "valor": "suelo"}]},
            {"cambios": []},
        ]
        for proposal in invalid:
            with self.subTest(proposal=proposal):
                with self.assertRaises(ValueError):
                    apply_proposal(RAW_CONFIG, proposal)
        self.assertEqual(RAW_CONFIG["KEYWORDS"], ["habilitación", "demolición", "obra nueva"])


class CommandLineTests(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.records_dir = self.data_dir / "seguimiento"
        self.records_dir.mkdir()
        self.output_dir = self.data_dir / "informes"
        self.config_path = self.data_dir / "config.json"
        self.config_path.write_text(json.dumps(RAW_CONFIG, ensure_ascii=False), encoding="utf-8")
        self.proposal_path = self.data_dir / "propuesta.json"
        self.proposal_path.write_text(
            json.dumps(
                {
                    "descripcion": "Retirar habilitación",
                    "cambios": [{"lista": "KEYWORDS", "operacion": "eliminar", "valor": "habilitación"}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        # Los registros se guardan en la subcarpeta "seguimiento".
        original_dir = self.data_dir
        self.data_dir = self.records_dir
        state = self.add_bulletin(7406, "13/07/2026", [record(1, RELEVANTE, "Otorga habilitación")])
        self.decide(state, 1, NO_RELEVANTE_CONFIRMADA)
        self.data_dir = original_dir

    def fingerprint(self):
        files = sorted(self.records_dir.glob("*.json")) + [self.config_path]
        return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}

    def run_cli(self, *args):
        return revisar_estrategias.main(
            [*args, "--datos", str(self.records_dir), "--salida", str(self.output_dir), "--config", str(self.config_path)]
        )

    def test_comparison_writes_reports_and_leaves_inputs_unchanged(self):
        before = self.fingerprint()

        exit_code = self.run_cli("comparar", "--propuesta", str(self.proposal_path))

        self.assertEqual(exit_code, 0)
        self.assertEqual(self.fingerprint(), before)
        report = next(self.output_dir.glob("*_comparacion.md")).read_text(encoding="utf-8")
        self.assertIn("Irrelevantes evitadas (decisión) | 1", report)
        self.assertTrue(list(self.output_dir.glob("*_comparacion.csv")))

    def test_term_report_is_written(self):
        exit_code = self.run_cli("terminos")

        self.assertEqual(exit_code, 0)
        report = next(self.output_dir.glob("*_terminos.md")).read_text(encoding="utf-8")
        self.assertIn("## Candidatos a revisión", report)
        self.assertIn("## En observación", report)
        self.assertIn("Tasa máx. (3/n)", report)
        # Un solo caso evaluado: queda en observacion, no como candidato.
        observation_section = report.split("## En observación")[1].split("## Términos con relevantes")[0]
        self.assertIn("habilitación", observation_section)

    def test_output_inside_records_folder_is_refused(self):
        exit_code = revisar_estrategias.main(
            ["terminos", "--datos", str(self.records_dir), "--salida", str(self.records_dir / "x"),
             "--config", str(self.config_path)]
        )

        self.assertEqual(exit_code, 2)
        self.assertFalse((self.records_dir / "x").exists())


if __name__ == "__main__":
    unittest.main()
