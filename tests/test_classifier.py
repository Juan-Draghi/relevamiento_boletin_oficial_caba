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

    def test_curated_law_match_accepts_number_without_thousands_dot(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Decreto",
                "sumario": "Sustituye el Anexo de la Ley 6927 y su modificatoria Ley 6942",
                "organismo": "Otro organismo",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn(
            "referencia_norma_curada: [Ll]ey(?: [Nn]°?)? ?6\\.?927",
            result.motivo_deteccion,
        )

    def test_curated_resolution_227_secgdu_26_matches_real_variants(self):
        # Caso real: Resolucion N° 252/SECGDU/26, BO 7489 (2026-11-05).
        expected_motivo = (
            "referencia_norma_curada: "
            "[Rr]esoluci[oó]n(?: [Nn]°?)? ?227(?:[-/]?GCABA)?[-/]?SECGDU[-/]?26"
        )
        sumarios = [
            "Prorroga la entrada en vigencia de la Resolución N° 227-SECGDU/26",
            "Modifica la Resolución N° 227/SECGDU/26",
            "Modifica la Resolucion 227/GCABA/SECGDU/26",
        ]
        for sumario in sumarios:
            with self.subTest(sumario=sumario):
                result = classify_norma(
                    {
                        "poder": "Poder Ejecutivo",
                        "tipo_norma": "Resolución",
                        "sumario": sumario,
                        "organismo": "Otro organismo",
                    },
                    self.config,
                )
                self.assertEqual(result.categoria_salida, RELEVANTE)
                self.assertIn(expected_motivo, result.motivo_deteccion)

    def test_curated_resolution_227_secgdu_26_does_not_match_neighbors(self):
        sumarios = [
            "Modifica la Resolución N° 228-SECGDU/26",
            "Modifica la Resolución N° 1227-SECGDU/26",
            "Modifica la Resolución N° 227-SECGDU/25",
        ]
        for sumario in sumarios:
            with self.subTest(sumario=sumario):
                result = classify_norma(
                    {
                        "poder": "Poder Ejecutivo",
                        "tipo_norma": "Resolución",
                        "sumario": sumario,
                        "organismo": "Otro organismo",
                    },
                    self.config,
                )
                self.assertFalse(
                    any("227" in m for m in result.motivo_deteccion if m.startswith("referencia_norma_curada:"))
                )

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
        self.assertIn("organismo_prioritario: DGROC", result.motivo_deteccion)

    def test_priority_organism_with_action_verb_without_norm_reference_goes_to_manual_review(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 123/DGROC/26",
                "sumario": "Aprueba nuevos criterios de aplicacion interna",
                "organismo": "Dirección General de Registro de Obras y Catastro",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, REVISION_MANUAL)
        self.assertIn("sumario_opaco_patron", result.motivo_deteccion)
        self.assertIn("organismo_prioritario: DGROC", result.motivo_deteccion)

    def test_priority_organism_with_norm_reference_without_action_verb_goes_to_manual_review(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "sumario": "Disposición 999/DGROC/25",
                "organismo": "Dirección General de Registro de Obras y Catastro",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, REVISION_MANUAL)
        self.assertIn("sumario_opaco_patron", result.motivo_deteccion)
        self.assertIn("organismo_prioritario: DGROC", result.motivo_deteccion)

    def test_priority_organism_sigla_in_norm_name_goes_to_manual_review(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 194/SSGOU/26",
                "sumario": "Sustituye, el Anexo I de la Resolución N° 339-SSGOU/22",
                "organismo": "Jefatura de Gabinete de Ministros",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, REVISION_MANUAL)
        self.assertIn("sumario_opaco_patron", result.motivo_deteccion)
        self.assertIn("organismo_prioritario: SSGOU", result.motivo_deteccion)

    def test_ssgou_public_space_case_is_relevant_by_conditional_keyword(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 320/SSGOU/26",
                "sumario": (
                    "Aprueba los lineamientos y requisitos para el expendio y/o venta de bebidas "
                    "no alcohólicas y/o servicio de cafetería en emplazamientos de puestos de venta "
                    "de diarios, revistas y afines en el espacio público"
                ),
                "organismo": "",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn("keyword_condicional_sumario: espacio público", result.motivo_deteccion)

    def test_dgfyco_demolition_case_is_relevant_by_direct_keyword(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Disposición",
                "nombre": "Disposición N° 374/DGFYCO/26",
                "sumario": (
                    "Aprueba Declaración Jurada de Corte Parcial de Suministro para Demolición "
                    "Parcial y la Declaración Jurada de: Inexistencia de Conexión de Gas"
                ),
                "organismo": "",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn("keyword_sumario: demolición", result.motivo_deteccion)

    def test_clubes_de_barrio_regularization_regime_is_relevant(self):
        # Omision identificada: BO 7458, Ley de Aprobacion Inicial N° 1740/LCABA/26.
        result = classify_norma(
            {
                "poder": "Poder Legislativo",
                "tipo_norma": "Ley de Aprobación Inicial",
                "nombre": "Ley de Aprobación Inicial N° 1740/LCABA/26",
                "sumario": (
                    "Crea el Régimen Especial de Adecuación y Regularización "
                    "para Clubes de Barrio."
                ),
                "organismo": "Legislatura de la Ciudad de Buenos Aires",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn(
            "keyword_sumario: régimen especial de adecuación y regularización",
            result.motivo_deteccion,
        )

    def test_club_subsidy_rendition_is_not_relevant(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 360/SECD/26",
                "sumario": (
                    "Aprueba la rendición de cuentas del subsidio otorgado "
                    "realizada por el Club Atlético Huracán"
                ),
                "organismo": "Jefatura de Gabinete de Ministros",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)

    def test_individual_consulta_obligatoria_is_not_relevant(self):
        # Caso real: BO 7415, acto individual de DGIUR sobre un inmueble.
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Disposición",
                "nombre": "Disposición N° 1251/DGIUR/26",
                "sumario": (
                    "Aprueba la Consulta Obligatoria de Obra Nueva a desarrollarse en el "
                    "inmueble sito en Almirante F. J. Segui 1227/29 y autoriza Localización "
                    "de Usos del Suelo"
                ),
                "organismo": "Jefatura de Gabinete de Ministros",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)

    def test_consulta_obligatoria_procedure_is_relevant_by_conditional_keyword(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 999/SECGDU/26",
                "sumario": "Aprueba el procedimiento para la tramitación de la Consulta Obligatoria",
                "organismo": "Jefatura de Gabinete de Ministros",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn("keyword_condicional_sumario: consulta obligatoria", result.motivo_deteccion)

    def test_individual_private_security_habilitacion_is_not_relevant(self):
        # Caso real: BO 7409, habilitacion individual de seguridad privada.
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Disposición",
                "nombre": "Disposición N° 191/DGSPCB/26",
                "sumario": (
                    "Concede habilitación para prestar servicios de seguridad privada "
                    "a la empresa Murallas SA"
                ),
                "organismo": "Ministerio de Seguridad",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)

    def test_habilitacion_procedure_is_relevant_by_conditional_keyword(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 999/AGC/26",
                "sumario": "Aprueba el procedimiento de habilitación de locales comerciales",
                "organismo": "Jefatura de Gabinete de Ministros",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn("keyword_condicional_sumario: habilitación", result.motivo_deteccion)

    def test_individual_surface_extension_is_not_relevant(self):
        # Caso real: BO 7414, autorizacion de DGIUR para un inmueble.
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Disposición",
                "nombre": "Disposición N° 1240/DGIUR/26",
                "sumario": (
                    "Autoriza Ampliación de Superficie de Usos del Suelo en el inmueble "
                    "sito en Av. Tornquist 6385t"
                ),
                "organismo": "Jefatura de Gabinete de Ministros",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)

    def test_surface_criteria_is_relevant_by_conditional_keyword(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 999/SECGDU/26",
                "sumario": "Establece los criterios para el cómputo de superficie cubierta",
                "organismo": "Jefatura de Gabinete de Ministros",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn("keyword_condicional_sumario: superficie", result.motivo_deteccion)

    def test_individual_environmental_certificate_renewal_is_not_relevant(self):
        # Caso real: BO 7422, renovacion de un certificado de APRA.
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 229/APRA/26",
                "sumario": "Renueva el Certificado de Aptitud Ambiental N° 21.791",
                "organismo": "Vicejefatura de Gobierno",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, NO_RELEVANTE)

    def test_environmental_certificate_procedure_is_relevant_by_conditional_keyword(self):
        result = classify_norma(
            {
                "poder": "Poder Ejecutivo",
                "tipo_norma": "Resolución",
                "nombre": "Resolución N° 999/APRA/26",
                "sumario": (
                    "Aprueba el procedimiento para la emisión del Certificado de "
                    "Aptitud Ambiental"
                ),
                "organismo": "Vicejefatura de Gobierno",
            },
            self.config,
        )

        self.assertEqual(result.categoria_salida, RELEVANTE)
        self.assertIn(
            "keyword_condicional_sumario: certificado de aptitud ambiental",
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
