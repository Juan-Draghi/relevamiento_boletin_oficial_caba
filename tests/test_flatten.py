import unittest

from bo_detector.flatten import flatten_normas_payload


class FlattenTests(unittest.TestCase):
    def test_flatten_obtener_boletin_payload(self):
        payload = {
            "boletin": {
                "numero": 7308,
                "fecha_publicacion": "19/02/2026",
                "url_boletin": "https://example.test/boletin.pdf",
            },
            "normas": {
                "normas": {
                    "Poder Ejecutivo": {
                        "Resolución": {
                            "Agencia Gubernamental de Control": [
                                {
                                    "nombre": "Resolución N° 96/AGC/25",
                                    "sumario": "Aprueba procedimiento",
                                    "id_norma": 1,
                                    "url_norma": "https://example.test/norma.pdf",
                                    "anexos": [
                                        {
                                            "nombre_anexo": "Anexo I",
                                            "filenet_firmado": "https://example.test/anexo.pdf",
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                }
            },
        }

        records = flatten_normas_payload(payload)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["poder"], "Poder Ejecutivo")
        self.assertEqual(records[0]["tipo_norma"], "Resolución")
        self.assertEqual(records[0]["organismo"], "Agencia Gubernamental de Control")
        self.assertEqual(records[0]["numero_boletin"], 7308)
        self.assertEqual(records[0]["anexos"][0]["url"], "https://example.test/anexo.pdf")


if __name__ == "__main__":
    unittest.main()

