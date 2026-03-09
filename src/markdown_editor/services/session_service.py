import os
from pathlib import Path


class SessionService:
    def __init__(self, config_dir):
        self.config_dir = Path(config_dir)
        self.session_dir = self.config_dir / "session"
        self.recovery_file = self.session_dir / "recovery.md"
        self.metadata_file = self.session_dir / "recovery.meta"

    def has_recovery_data(self):
        return self.recovery_file.exists() and self.recovery_file.stat().st_size > 0

    def save_recovery(self, text, current_file=None):
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.recovery_file.write_text(text, encoding="utf-8")
        source = current_file or ""
        self.metadata_file.write_text(source, encoding="utf-8")

    def load_recovery(self):
        if not self.has_recovery_data():
            return None

        source = ""
        if self.metadata_file.exists():
            source = self.metadata_file.read_text(encoding="utf-8").strip()

        return {
            "text": self.recovery_file.read_text(encoding="utf-8"),
            "source": source,
        }

    def clear_recovery(self):
        for file_path in (self.recovery_file, self.metadata_file):
            if file_path.exists():
                file_path.unlink()
