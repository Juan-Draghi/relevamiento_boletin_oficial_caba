from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import desktop_app.app as desktop_module
from bo_detector.classifier import NO_RELEVANTE
from bo_detector.review_store import upsert_analysis


class DesktopAppTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.data_dir = Path(self.temporary_directory.name)
        self.data_dir_patcher = patch.object(desktop_module, "REVIEW_DATA_DIR", self.data_dir)
        self.data_dir_patcher.start()
        self.client = desktop_module.app.test_client()

    def tearDown(self):
        self.data_dir_patcher.stop()
        self.temporary_directory.cleanup()

    def test_index_has_review_and_indicator_tabs_without_config_editor(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('data-tab-target="review"', html)
        self.assertIn('data-tab-target="indicators"', html)
        self.assertIn('id="no-relevant-body"', html)
        self.assertIn('id="discarded-body"', html)
        self.assertNotIn('id="config-form"', html)
        self.assertIn('id="bulletin-control"', html)
        self.assertIn('type="checkbox" value="PENDIENTE"', html)
        self.assertIn('id="bulletin-save-status"', html)
        self.assertIn('id="indicator-volume-grid"', html)
        self.assertIn('id="indicator-performance-grid"', html)
        self.assertIn('class="results-count"', html)
        self.assertIn('0 normas', html)
        self.assertNotIn('id="bulletin-observations"', html)
        self.assertNotIn('id="week-notes-form"', html)
        self.assertNotIn("Ajustes derivados y observaciones", html)
        self.assertNotIn("Guardar configuración", html)

        app_js = (Path(desktop_module.__file__).parent / "static" / "app.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("metric-card__description", app_js)
        self.assertIn(
            "Porcentaje de normas procesadas que ya tienen una decisión profesional.",
            app_js,
        )

    def test_configuration_endpoint_is_disabled(self):
        response = self.client.post("/api/config", data={"KEYWORDS": "prueba"})

        self.assertEqual(response.status_code, 404)
        self.assertIn("retirada", response.get_json()["message"])

    def test_empty_week_indicators_report_no_activity(self):
        response = self.client.get("/api/indicators?week=2026-W29")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["control_complementario"], "No utilizado")
        self.assertEqual(payload["normas_procesadas"], 0)
        self.assertEqual(payload["falsos_negativos"], "N/D")
        self.assertEqual(payload["cobertura_validacion"], "No utilizado")
        self.assertEqual(payload["precision_automatica"], "N/D")

    def test_false_negative_can_be_registered_through_api(self):
        state = upsert_analysis(
            self.data_dir,
            {"numero_boletin": 7400, "fecha_publicacion": "13/07/2026"},
            [
                {
                    "id_norma": 99,
                    "numero_boletin": 7400,
                    "fecha_publicacion": "13/07/2026",
                    "poder": "Poder Ejecutivo",
                    "tipo_norma": "Resolución",
                    "organismo": "Organismo",
                    "nombre": "Resolución 99",
                    "sumario": "Caso de prueba",
                    "url_norma": "",
                    "motivo_deteccion": [],
                    "categoria_salida": NO_RELEVANTE,
                }
            ],
        )

        response = self.client.post(
            "/api/review/norma",
            json={
                "semana": state["semana"],
                "boletin_clave": state["boletin_clave"],
                "clave_registro": "id_norma:99",
                "decision_manual": "RELEVANTE_CONFIRMADA",
                "observacion": "La revisión profesional confirmó su relevancia.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["es_falso_negativo"])

    def test_week_notes_require_a_list_of_adjustments(self):
        response = self.client.post(
            "/api/review/semana",
            json={
                "semana": "2026-W29",
                "ajustes_derivados": "LOG-2026-07-13",
                "observaciones": "",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("lista", response.get_json()["message"])


if __name__ == "__main__":
    unittest.main()

