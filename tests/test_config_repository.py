import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markdown_editor.repositories.config_repository import ConfigRepository


class ConfigRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = Path(self.temp_dir.name) / "config.json"
        self.repository = ConfigRepository(str(self.config_file))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_returns_saved_json(self):
        self.config_file.write_text(json.dumps({"language": "es"}), encoding="utf-8")

        loaded = self.repository.load()

        self.assertEqual(loaded["language"], "es")

    def test_save_writes_atomic_json_file(self):
        payload = {"render_style": "slate"}

        self.repository.save(payload)

        reloaded = json.loads(self.config_file.read_text(encoding="utf-8"))
        self.assertEqual(reloaded, payload)


if __name__ == "__main__":
    unittest.main()
