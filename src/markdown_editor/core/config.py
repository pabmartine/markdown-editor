import copy
import json
import os

from .constants import DEFAULT_CONFIG
from ..repositories.config_repository import ConfigRepository

STYLE_ALIASES = {
    "github": "slate",
    "github-light": "ivory",
    "github-dark": "nocturne",
    "gitlab": "ember",
}


def get_config_dir():
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return os.path.join(config_home, "markdown-editor")
    return os.path.join(os.path.expanduser("~"), ".config", "markdown-editor")


CONFIG_DIR = get_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


class Config:
    def __init__(self):
        self.repository = ConfigRepository(CONFIG_FILE)
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        try:
            self.load_config()
        except Exception:
            pass
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                loaded_config = self.repository.load()
                migrated = False
                if "render_style" in loaded_config:
                    normalized_style = STYLE_ALIASES.get(
                        loaded_config["render_style"],
                        loaded_config["render_style"],
                    )
                    migrated = normalized_style != loaded_config["render_style"]
                    loaded_config["render_style"] = normalized_style
                self.config.update(loaded_config)
                if migrated:
                    self.save_config()
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading configuration: {e}")
    
    def save_config(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            self.repository.save(self.config)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()
