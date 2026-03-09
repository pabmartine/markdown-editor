import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markdown_editor.ui.support.editor_actions import EditorActionsMixin
from markdown_editor.ui.support.search import SearchMixin


class EditorActionsTest(unittest.TestCase):
    def test_unordered_list_continues_with_same_bullet(self):
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("- item"), "- ")
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("  * item"), "  * ")
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("    + item"), "    + ")

    def test_ordered_list_continues_with_next_number(self):
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("1. item"), "2. ")
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("  4. item"), "  5. ")

    def test_task_list_continues_with_unchecked_box(self):
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("- [ ] item"), "- [ ] ")
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("  - [x] done"), "  - [ ] ")

    def test_empty_list_item_stops_list(self):
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("- "), "")
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("3. "), "")
        self.assertEqual(EditorActionsMixin.get_list_continuation_prefix("- [ ] "), "")

    def test_non_list_line_does_not_continue(self):
        self.assertIsNone(EditorActionsMixin.get_list_continuation_prefix("plain text"))

    def test_build_markdown_table_uses_requested_size(self):
        table = EditorActionsMixin.build_markdown_table(3, 2)

        self.assertIn("| Header 1 | Header 2 |", table)
        self.assertIn("| --- | --- |", table)
        self.assertIn("| Cell 1-1 | Cell 1-2 |", table)
        self.assertIn("| Cell 2-1 | Cell 2-2 |", table)

    def test_normalize_search_selection_collapses_whitespace(self):
        self.assertEqual(SearchMixin.normalize_search_selection("  hello \n world  "), "hello world")


if __name__ == "__main__":
    unittest.main()
