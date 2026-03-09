import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markdown_editor.core.config import Config


class ConfigTest(unittest.TestCase):
    def test_load_normalizes_legacy_render_style_aliases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_file.write_text(json.dumps({"render_style": "github-dark"}), encoding="utf-8")

            with mock.patch("markdown_editor.core.config.CONFIG_FILE", str(config_file)):
                config = Config()

            self.assertEqual(config.get("render_style"), "nocturne")


if __name__ == "__main__":
    unittest.main()
