import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markdown_editor.services.html_preview import HtmlPreviewService


class HtmlPreviewServiceTest(unittest.TestCase):
    def test_render_body_uses_standard_markdown_html(self):
        rendered = HtmlPreviewService.render_body(
            "# Title\n\n| A | B |\n| - | - |\n| 1 | 2 |"
        )

        self.assertIn("<h1>Title</h1>", rendered)
        self.assertIn("<table>", rendered)
        self.assertIn("<th>A</th>", rendered)

    def test_render_body_transforms_task_lists(self):
        rendered = HtmlPreviewService.render_body("- [x] Done\n- [ ] Pending")

        self.assertIn('class="task-list"', rendered)
        self.assertIn('class="task-list-item"', rendered)
        self.assertIn('checked=""', rendered)
        self.assertIn("Pending", rendered)

    def test_render_document_includes_theme_css(self):
        document = HtmlPreviewService.render_document(
            "## Subtitle",
            title="Doc",
            render_style="nocturne",
            max_width_chars=72,
        )

        self.assertIn("<title>Doc</title>", document)
        self.assertIn("color-scheme: dark", document)
        self.assertIn("max-width: 72ch;", document)
        self.assertIn("<h2>Subtitle</h2>", document)


if __name__ == "__main__":
    unittest.main()
