from pathlib import Path
import unittest

import desktop_app.app as desktop_module


class CompactInterfaceTests(unittest.TestCase):
    def test_index_uses_compact_review_lists(self):
        response = desktop_module.app.test_client().get("/")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="review-workspace"', html)
        self.assertIn('class="review-list" id="primary-results-body"', html)
        self.assertIn('class="review-list review-list--secondary" id="no-relevant-body"', html)
        self.assertIn('class="review-list review-list--secondary" id="discarded-body"', html)
        self.assertNotIn('class="results-table"', html)
        self.assertNotIn("Configuración activa", html)

    def test_javascript_renders_cards_and_filters_searchable_elements(self):
        javascript_path = Path(desktop_module.__file__).parent / "static" / "app.js"
        javascript = javascript_path.read_text(encoding="utf-8")

        self.assertIn('<article data-result-key="${escapeHtml(result.clave_registro)}"', javascript)
        self.assertIn("review-card--false-negative", javascript)
        self.assertIn('querySelectorAll("[data-search]")', javascript)
        self.assertNotIn('querySelectorAll("tr[data-search]")', javascript)


if __name__ == "__main__":
    unittest.main()
