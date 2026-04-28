import unittest

from bo_detector.classifier import NO_RELEVANTE, RELEVANTE, REVISION_MANUAL, classify_norma
from bo_detector.config import load_config


class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()

    def test_keyword_match_is_accent_insensitive(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "sumario": "Aprueba modificacion del Codigo Urbanistico",
                "organismo": "Otro organismo",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn("keyword_sumario: código urbanístico", result.motivo_deteccion)

    def test_curated_norm_match_is_relevant(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Decreto",
                "sumario": "Modifícase el Decreto 116/25",
                "organismo": "Otro organismo",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertTrue(any(m.startswith("referencia_norma_curada:") for m in result.motivo_deteccion))

    def test_priority_organism_alone_is_not_manual_review(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "sumario": "Aprueba procedimiento interno",
                "organismo": "Dirección General de Registro de Obras y Catastro",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)

    def test_priority_organism_with_opaque_action_goes_to_manual_review(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "sumario": "Modifícase la Disposición 999/DGROC/25",
                "organismo": "Dirección General de Registro de Obras y Catastro",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, REVISION_MANUAL)
        self.assertIn("sumario_opaco_patron", result.motivo_deteccion)
        self.assertIn(
            "organismo_prioritario: Dirección General de Registro de Obras y Catastro",
            result.motivo_deteccion,
        )

    def test_short_summary_alone_is_not_manual_review(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "sumario": "Aprueba procedimiento",
                "organismo": "Otro organismo",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)

    def test_no_signal_is_not_relevant(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "sumario": "Aprueba el programa anual de capacitaciones internas administrativas",
                "organismo": "Otro organismo",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)
        self.assertEqual(result.motivo_deteccion, ())

    def test_public_space_individual_permit_is_not_relevant(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "sumario": "Otorga permiso de uso temporario y revocable del espacio público para emplazar andamios",
                "organismo": "Otro organismo",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)

    def test_public_space_normative_change_is_relevant(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "sumario": "Modifica los requisitos para el otorgamiento de permisos de uso del espacio público",
                "organismo": "Otro organismo",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn(
            "keyword_condicional_sumario: uso del espacio público",
            result.motivo_deteccion,
        )

    def test_structural_filter_discards_excluded_power(self):
        result = classify_norma(
            {
                "poder": "Poder Judicial",
                "tipo_norma": "Resolución",
                "sumario": "Aprueba el Código Urbanístico",
                "organismo": "Otro organismo",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, "DESCARTADA_FILTRO_ESTRUCTURAL")

    def test_aclaracion_type_is_included(self):
        result = classify_norma(
            {
                "poder": "Poder Legislativo",
                "tipo_norma": "Aclaración",
                "sumario": "Ley Impositiva año 2026.",
                "organismo": "Legislatura de la Ciudad de Buenos Aires",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn("keyword_sumario: ley impositiva", result.motivo_deteccion)


if __name__ == "__main__":
    unittest.main()
