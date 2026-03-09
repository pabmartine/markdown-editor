import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markdown_editor.services.rendering import AirRenderer
from markdown_editor.services.rendering import ImprovedRenderer
from markdown_editor.services.rendering import SlateRenderer


class RendererTest(unittest.TestCase):
    def test_markdown_extensions_do_not_enable_non_standard_line_breaks_or_smart_punctuation(self):
        renderer = ImprovedRenderer()

        extensions = renderer.get_markdown_extensions()

        self.assertNotIn("nl2br", extensions)
        self.assertNotIn("smarty", extensions)

    def test_ordered_lists_keep_real_numbers(self):
        renderer = ImprovedRenderer()

        rendered = renderer._html_to_pango("<ol><li>One</li><li>Two</li></ol>")

        self.assertIn("1. ", rendered)
        self.assertIn("2. ", rendered)

    def test_image_alt_text_is_escaped(self):
        renderer = ImprovedRenderer()

        rendered = renderer._html_to_pango('<p><img alt="<b>x</b>" src="image.png"></p>')

        self.assertIn("&lt;b&gt;x&lt;/b&gt;", rendered)

    def test_strikethrough_renders_in_themed_renderer(self):
        renderer = SlateRenderer()

        rendered = renderer._basic_render("~~tachado~~")

        self.assertIn("<s>tachado</s>", rendered)

    def test_themed_renderer_renders_deep_headings_without_markdown_dependency(self):
        renderer = SlateRenderer()

        rendered = renderer._basic_render("#### Heading 4\n##### Heading 5\n###### Heading 6")

        self.assertIn("Heading 4", rendered)
        self.assertIn("Heading 5", rendered)
        self.assertIn("Heading 6", rendered)
        self.assertNotIn("#### Heading 4", rendered)

    def test_themed_renderer_strips_optional_closing_hashes_from_headings(self):
        renderer = SlateRenderer()

        rendered = renderer._basic_render("### Heading ###\n#### Another ####")

        self.assertIn("Heading", rendered)
        self.assertIn("Another", rendered)
        self.assertNotIn("Heading ###", rendered)
        self.assertNotIn("Another ####", rendered)

    def test_air_renderer_renders_all_heading_levels(self):
        renderer = AirRenderer()

        rendered = renderer._basic_render(
            "### Heading 3\n#### Heading 4\n##### Heading 5\n###### Heading 6"
        )

        self.assertIn("Heading 3", rendered)
        self.assertIn("Heading 4", rendered)
        self.assertIn("Heading 5", rendered)
        self.assertIn("Heading 6", rendered)
        self.assertNotIn("### Heading 3", rendered)
        self.assertNotIn("#### Heading 4", rendered)
        self.assertNotIn("##### Heading 5", rendered)
        self.assertNotIn("###### Heading 6", rendered)


if __name__ == "__main__":
    unittest.main()
