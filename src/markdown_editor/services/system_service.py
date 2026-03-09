import os

from ..core.constants import APP_VERSION
from ..core.i18n import translate as _
from .rendering import ImprovedRenderer


class SystemInstaller:
    def __init__(self):
        self.desktop_file_content = """[Desktop Entry]
Name=Markdown Editor
Comment=Markdown editor with real-time preview
Exec=python3 {script_path} %F
Icon=text-editor
Terminal=false
Type=Application
Categories=Office;TextEditor;
MimeType=text/markdown;text/x-markdown;
"""

    def install_desktop_file(self, script_path):
        desktop_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(desktop_dir, exist_ok=True)
        desktop_file = os.path.join(desktop_dir, "markdown-editor.desktop")

        with open(desktop_file, "w", encoding="utf-8") as handle:
            handle.write(self.desktop_file_content.format(script_path=script_path))

        os.chmod(desktop_file, 0o755)
        print(f"Desktop file installed at: {desktop_file}")
        return True

    def check_dependencies(self):
        dependencies = {
            "gtk": ("gi.repository", "Gtk"),
            "adwaita": ("gi.repository", "Adw"),
            "pango": ("gi.repository", "Pango"),
            "gdk": ("gi.repository", "Gdk"),
            "glib": ("gi.repository", "GLib"),
            "gio": ("gi.repository", "Gio"),
            "webkit": ("gi.repository", "WebKit"),
        }
        optional_deps = {
            "markdown-it-py": ("markdown_it", None),
            "pygments": ("pygments", None),
            "markdown": ("markdown", None),
        }

        print("Checking dependencies...")
        all_ok = True

        for name, (module, attr) in dependencies.items():
            try:
                if attr:
                    imported = __import__(module, fromlist=[attr])
                    getattr(imported, attr)
                else:
                    __import__(module)
                print(f"✓ {name}: OK")
            except ImportError:
                print(f"✗ {name}: MISSING")
                all_ok = False

        print("\nOptional dependencies:")
        for name, (module, _attr) in optional_deps.items():
            try:
                __import__(module)
                print(f"✓ {name}: OK")
            except ImportError:
                print(f"⚠ {name}: Not available")

        return all_ok


class DebugUtils:
    @staticmethod
    def enable_debug_logging():
        import logging

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @staticmethod
    def print_system_info():
        import platform

        print("=== SYSTEM INFORMATION ===")
        print(f"System: {platform.system()} {platform.release()}")
        print(f"Python: {platform.python_version()}")
        print(f"Architecture: {platform.machine()}")

        try:
            import gi

            print(f"PyGObject: {gi.__version__}")
        except Exception:
            print("PyGObject: Not available")

        print("================================")

    @staticmethod
    def run_performance_test():
        import time

        print("Running performance test...")

        test_text = f"# {_('Test')}\n\n" + f"{_('Test paragraph')}. " * 100
        renderer = ImprovedRenderer()

        start_time = time.time()
        for iteration in range(100):
            renderer.render_text(test_text)
        end_time = time.time()
        print(f"Rendering (100 iterations): {end_time - start_time:.3f}s")

        from .document_service import DocumentService

        start_time = time.time()
        for iteration in range(1000):
            DocumentService.count_words(test_text)
        end_time = time.time()
        print(f"Word counting (1000 iterations): {end_time - start_time:.3f}s")


def build_version_string():
    return APP_VERSION
