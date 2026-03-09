import argparse
import os

from ..core.constants import APP_VERSION
from ..core.i18n import translate as _
from ..services.rendering import RendererFactory


def parse_command_line_args():
    parser = argparse.ArgumentParser(description=_("Advanced Markdown Editor"))
    parser.add_argument("files", nargs="*", help=_("Files to open"))
    parser.add_argument("--vim", action="store_true", help=_("Start in Vim mode"))
    parser.add_argument("--theme", choices=RendererFactory.get_available_styles(), help=_("Editor theme"))
    parser.add_argument("--auto-save", type=int, metavar="SECONDS", help=_("Enable auto-save with interval in seconds"))
    parser.add_argument("--version", action="version", version=APP_VERSION)
    parser.add_argument("--debug", action="store_true", help=_("Enable debug mode"))
    parser.add_argument("--install-desktop", action="store_true", help=_("Install desktop file"))
    parser.add_argument("--test", action="store_true", help=_("Run tests"))
    return parser.parse_args()


def apply_cli_options(app, args):
    if hasattr(app, "win") and app.win:
        if args.theme:
            app.win.config.set("render_style", RendererFactory.normalize_style_name(args.theme))
            app.win.apply_render_style()

        if args.vim:
            app.win.config.set("vim_mode", True)

        for file_path in args.files:
            if os.path.exists(file_path):
                app.win.load_file(file_path)
                break
