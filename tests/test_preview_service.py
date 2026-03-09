import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markdown_editor.services.preview_service import PreviewService


class PreviewServiceTest(unittest.TestCase):
    def test_parse_blocks_splits_markdown_code_table_and_image(self):
        text = (
            "# Title\n\n"
            "```python\nprint('hi')\n```\n\n"
            "| Name | Value |\n"
            "| --- | --- |\n"
            "| One | 1 |\n\n"
            "![Alt](image.png)\n"
        )

        blocks = PreviewService.parse_blocks(text)

        self.assertEqual([block.kind for block in blocks], ["markdown", "code", "table", "image"])
        self.assertEqual(blocks[1].language, "python")
        self.assertEqual(blocks[1].text, "print('hi')")
        self.assertEqual(blocks[2].rows[0], ("Name", "Value"))
        self.assertEqual(blocks[2].rows[1], ("One", "1"))
        self.assertEqual(blocks[2].alignments, ("left", "left"))
        self.assertEqual(blocks[3].text, "image.png")
        self.assertEqual(blocks[3].alt, "Alt")

    def test_parse_blocks_keeps_plain_markdown_when_not_special(self):
        text = "Paragraph\n\n- item\n- item 2"

        blocks = PreviewService.parse_blocks(text)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].kind, "markdown")
        self.assertEqual(blocks[1].kind, "list")

    def test_parse_blocks_supports_image_destinations_with_title_or_angle_brackets(self):
        text = '![Chart](<images/chart one.png> "caption")\n\n![Alt]("images/two.png")'

        blocks = PreviewService.parse_blocks(text)

        self.assertEqual([block.kind for block in blocks], ["image", "image"])
        self.assertEqual(blocks[0].text, "images/chart one.png")
        self.assertEqual(blocks[1].text, "images/two.png")

    def test_parse_blocks_supports_task_lists_and_blockquotes(self):
        text = "- [ ] One\n  - [x] Two\n\n> Quote line 1\n> Quote line 2"

        blocks = PreviewService.parse_blocks(text)

        self.assertEqual([block.kind for block in blocks], ["tasks", "blockquote"])
        self.assertEqual(blocks[0].items[0], (0, False, "One"))
        self.assertEqual(blocks[0].items[1], (2, True, "Two"))
        self.assertEqual(blocks[1].text, "Quote line 1\nQuote line 2")

    def test_parse_blocks_extracts_table_alignment(self):
        text = "| A | B | C |\n| :--- | :---: | ---: |\n| 1 | 2 | 3 |"

        blocks = PreviewService.parse_blocks(text)

        self.assertEqual(blocks[0].kind, "table")
        self.assertEqual(blocks[0].alignments, ("left", "center", "right"))

    def test_parse_blocks_supports_nested_lists(self):
        text = "- One\n  - Two\n  1. Three"

        blocks = PreviewService.parse_blocks(text)

        self.assertEqual([block.kind for block in blocks], ["list"])
        self.assertEqual(blocks[0].items[0], (0, False, "- One"))
        self.assertEqual(blocks[0].items[1], (2, False, "- Two"))
        self.assertEqual(blocks[0].items[2], (2, True, "1. Three"))

    def test_parse_blocks_supports_thematic_breaks(self):
        text = "Paragraph\n\n---\n\nNext"

        blocks = PreviewService.parse_blocks(text)

        self.assertEqual([block.kind for block in blocks], ["markdown", "rule", "markdown"])


if __name__ == "__main__":
    unittest.main()
