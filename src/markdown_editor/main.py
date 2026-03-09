import os
import sys
import traceback

_ = lambda text: text

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
except Exception as exc:
    print(_("Could not import GTK4 and Adwaita."))
    print(_("Make sure you have python3-gi, libgtk-4-dev and libadwaita-1-dev installed"))
    print(f"{_('Specific error')}: {exc}")
    raise SystemExit(1)

from .app import MarkdownApp
from .cli.arguments import parse_command_line_args
from .cli.checks import run_basic_tests
from .core.i18n import setup_locale, translate as _
from .services.system_service import DebugUtils, SystemInstaller


def main():
    try:
        args = parse_command_line_args()
    except SystemExit:
        return 0

    if args.debug:
        DebugUtils.print_system_info()
        DebugUtils.enable_debug_logging()

    installer = SystemInstaller()
    if not installer.check_dependencies():
        print(f"\n{_('ERROR: Missing required dependencies.')}")
        print(_("Check the installation guide for more information."))
        return 1

    if args.install_desktop:
        script_path = os.path.abspath(sys.argv[0])
        if installer.install_desktop_file(script_path):
            print(_("System integration completed."))
        return 0

    if args.test:
        run_basic_tests()
        DebugUtils.run_performance_test()
        return 0

    try:
        app = MarkdownApp(cli_args=args)
        return app.run(sys.argv)
    except KeyboardInterrupt:
        print(f"\n{_('Application interrupted by user.')}")
        return 0
    except Exception as exc:
        print(f"{_('Fatal error in application')}: {exc}")
        traceback.print_exc()
        return 1


def main_entrypoint():
    setup_locale()
    if sys.version_info < (3, 6):
        print(_("ERROR: Python 3.6 or higher required"))
        return 1
    return main()
