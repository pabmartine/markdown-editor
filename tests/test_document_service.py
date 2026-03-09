import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markdown_editor.services.document_service import DocumentService


class DocumentServiceTest(unittest.TestCase):
    def test_extract_headers_preserves_level_title_and_line(self):
        text = "# Title\n\n## Subtitle\nText"

        headers = DocumentService.extract_headers(text)

        self.assertEqual(len(headers), 2)
        self.assertEqual(headers[0].level, 1)
        self.assertEqual(headers[0].title, "Title")
        self.assertEqual(headers[0].line, 1)
        self.assertEqual(headers[1].level, 2)
        self.assertEqual(headers[1].line, 3)

    def test_count_words_skips_code_and_links_markup(self):
        text = "# Title\nText with **bold** and [link](https://example.com)\n```py\nignored\n```"

        self.assertEqual(DocumentService.count_words(text), 6)

    def test_compute_stats_returns_lines_words_and_size(self):
        stats = DocumentService.compute_stats("one two\nthree")

        self.assertEqual(stats.lines, 2)
        self.assertEqual(stats.words, 3)
        self.assertEqual(stats.characters, len("one two\nthree"))
        self.assertEqual(stats.size_bytes, len("one two\nthree".encode("utf-8")))
        self.assertEqual(stats.headers, 0)
        self.assertEqual(stats.reading_time_minutes, 1)

    def test_find_current_header_returns_last_header_before_line(self):
        text = "# Title\nText\n## Section\nMore\n### Subsection\nBody"

        current = DocumentService.find_current_header(text, 4)

        self.assertIsNotNone(current)
        self.assertEqual(current.title, "Section")
        self.assertEqual(current.line, 3)


if __name__ == "__main__":
    unittest.main()
