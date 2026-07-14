import json
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DataVersioningPolicyTests(unittest.TestCase):
    def test_real_weekly_json_is_ignored_and_example_is_versionable(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("data/seguimiento/*.json", gitignore)
        self.assertIn("!data/seguimiento/ejemplo_seguimiento.json", gitignore)

    def test_sanitized_example_has_the_weekly_schema(self):
        example_path = PROJECT_ROOT / "data" / "seguimiento" / "ejemplo_seguimiento.json"
        document = json.loads(example_path.read_text(encoding="utf-8"))

        self.assertEqual(document["schema_version"], 1)
        self.assertEqual(document["periodo"]["clave"], "2099-W02")
        self.assertEqual(len(document["boletines"]), 1)

        bulletin = document["boletines"]["boletin:0000"]
        norm = bulletin["normas"]["id_norma:1"]
        self.assertEqual(norm["decision_manual"], "RELEVANTE_CONFIRMADA")
        self.assertEqual(norm["categoria_automatica_original"], "RELEVANTE")


if __name__ == "__main__":
    unittest.main()
