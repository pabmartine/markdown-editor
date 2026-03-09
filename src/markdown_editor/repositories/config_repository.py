import json
import os
import tempfile


class ConfigRepository:
    def __init__(self, config_file):
        self.config_file = config_file

    def load(self):
        if not os.path.exists(self.config_file):
            return {}

        with open(self.config_file, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, config):
        directory = os.path.dirname(self.config_file)
        os.makedirs(directory, exist_ok=True)

        with tempfile.NamedTemporaryFile("w", dir=directory, delete=False, encoding="utf-8") as temp_file:
            json.dump(config, temp_file, indent=2, ensure_ascii=False)
            temp_name = temp_file.name

        os.replace(temp_name, self.config_file)
