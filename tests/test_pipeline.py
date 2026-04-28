import unittest

from bo_detector.pipeline import classify_boletin_payload


class PipelineTests(unittest.TestCase):
    def test_classify_boletin_payload_filters_not_relevant_by_default(self):
        payload = {
            "normas": {
                "normas": {
                    "Poder Ejecutivo": {
                        "Resolución": {
                            "Otro organismo": [
                                {
                                    "poder": "Poder Ejecutivo",
                                    "tipo_norma": "Resolución",
                                    "nombre": "Resolución N° 1",
                                    "sumario": "Aprueba el Código Urbanístico",
                                },
                                {
                                    "poder": "Poder Ejecutivo",
                                    "tipo_norma": "Resolución",
                                    "nombre": "Resolución N° 2",
                                    "sumario": "Aprueba el programa anual de capacitaciones internas administrativas",
                                },
                            ]
                        }
                    }
                }
            }
        }

        records = classify_boletin_payload(payload)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["nombre"], "Resolución N° 1")
        self.assertEqual(records[0]["categoria_salida"], "RELEVANTE")


if __name__ == "__main__":
    unittest.main()
