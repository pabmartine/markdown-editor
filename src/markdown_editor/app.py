import os
import traceback

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

try:
    gi.require_version("WebKit", "6.0")
    from gi.repository import WebKit
    WEBKIT_AVAILABLE = True
except Exception:
    WebKit = None
    WEBKIT_AVAILABLE = False

from gi.repository import Adw, Gio, GLib, Gtk

from .core.constants import APP_ID
from .core.i18n import get_available_languages, translate as _
from .cli.arguments import apply_cli_options
from .services.export_service import ExportService
from .services.rendering import RendererFactory
from .services.system_service import build_version_string
from .ui.window import MarkdownEditorWindow


COLOR_SCHEMES = ["default", "light", "dark"]


class MarkdownApp(Adw.Application):
    def __init__(self, cli_args=None):
        try:
            super().__init__(
                application_id="com.pabmartine.MarkdownEditor",
                flags=Gio.ApplicationFlags.DEFAULT_FLAGS
            )
            self.cli_args = cli_args
            self.connect("activate", self.on_activate)
            self.setup_actions()
        except Exception as e:
            print(f"Error initializing application: {e}")
            traceback.print_exc()
            raise

    def setup_actions(self):
        print_action = Gio.SimpleAction.new("print", None)
        print_action.connect("activate", self.on_print)
        self.add_action(print_action)
        self.set_accels_for_action("app.print", ["<Control>p"])
        self.set_accels_for_action("app.preferences", ["<Control>comma"])
        self.set_accels_for_action("app.shortcuts", ["<Control>question"])
        
        language_action = Gio.SimpleAction.new_stateful(
            "language", GLib.VariantType.new("s"), GLib.Variant("s", "auto")
        )
        language_action.connect("activate", self.on_language_changed)
        self.add_action(language_action)

        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)

        export_html_action = Gio.SimpleAction.new("export_html", None)
        export_html_action.connect("activate", self.on_export_html)
        self.add_action(export_html_action)

        export_pdf_action = Gio.SimpleAction.new("export_pdf", None)
        export_pdf_action.connect("activate", self.on_export_pdf)
        self.add_action(export_pdf_action)

        syntax_help_action = Gio.SimpleAction.new("syntax_help", None)
        syntax_help_action.connect("activate", self.on_syntax_help)
        self.add_action(syntax_help_action)

        shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
        shortcuts_action.connect("activate", self.on_shortcuts)
        self.add_action(shortcuts_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
    
    def _toast(self, message):
        if hasattr(self, "win") and hasattr(self.win, "show_toast"):
            self.win.show_toast(message)
        else:
            print(message)

    def on_print(self, action, parameter):
        if not WEBKIT_AVAILABLE:
            self._toast(_("Printing needs WebKitGTK, which is not available"))
            return

        def run_print(webview):
            try:
                print_operation = WebKit.PrintOperation.new(webview)
                print_operation.run_dialog(self.win)
                print_operation.run_dispose()
            except Exception as e:
                print(f"Error printing: {e}")
                self._toast(_("Could not print the document"))

        self.prepare_preview_webview_for_printing(run_print)
    
    def on_language_changed(self, action, parameter):
        language_code = parameter.get_string()
        action.set_state(parameter)
        if hasattr(self, "win"):
            self.win.change_language(language_code)
    
    def on_preferences(self, action, parameter):
        if hasattr(self, "win"):
            self.show_preferences_dialog()

    def show_preferences_dialog(self):
        if not Adw:
            print("Adwaita not available for preferences")
            return

        # AdwPreferencesDialog manages its own presentation, so the manual
        # transient/modal/size handling and the reuse bookkeeping go away.
        dialog = Adw.PreferencesDialog()

        page = Adw.PreferencesPage()
        page.set_title(_("General"))

        language_group = self.create_language_preferences()
        page.add(language_group)

        appearance_group = self.create_appearance_preferences()
        page.add(appearance_group)

        editor_group = self.create_editor_preferences()
        page.add(editor_group)

        render_group = self.create_render_preferences()
        page.add(render_group)

        autosave_group = self.create_autosave_preferences()
        page.add(autosave_group)

        dialog.add(page)
        dialog.present(self.win)

    def create_language_preferences(self):
        language_group = Adw.PreferencesGroup()
        language_group.set_title(_("Language"))

        language_row = Adw.ComboRow()
        language_row.set_title(_("Interface language"))
        language_row.set_subtitle(_("Change application language"))
        
        language_model = Gtk.StringList()
        available_languages = get_available_languages()
        
        for lang_code, lang_name in available_languages:
            language_model.append(lang_name)
        
        language_row.set_model(language_model)

        current_lang = self.win.current_language
        lang_codes = [lang[0] for lang in available_languages]
        if current_lang in lang_codes:
            language_row.set_selected(lang_codes.index(current_lang))
        else:
            language_row.set_selected(0)  # Default to auto-detect

        language_row.connect("notify::selected", self.on_language_row_changed)
        language_group.add(language_row)
        
        return language_group

    def create_appearance_preferences(self):
        appearance_group = Adw.PreferencesGroup()
        appearance_group.set_title(_("Appearance"))

        # Three states, so "follow the system" is expressible. The old boolean
        # mapped "off" to FORCE_LIGHT, overriding a dark desktop.
        style_row = Adw.ComboRow()
        style_row.set_title(_("Style"))
        style_row.set_subtitle(_("Follow the system preference, or force one"))
        style_model = Gtk.StringList()
        for label in (_("Follow System"), _("Light"), _("Dark")):
            style_model.append(label)
        style_row.set_model(style_model)
        style_row.set_selected(COLOR_SCHEMES.index(self.win.get_color_scheme()))
        style_row.connect("notify::selected", self.on_color_scheme_changed)
        appearance_group.add(style_row)
        
        return appearance_group

    def create_editor_preferences(self):
        editor_group = Adw.PreferencesGroup()
        editor_group.set_title(_("Editor"))

        font_row = Adw.SpinRow.new_with_range(1, 200, 1)
        font_row.set_title(_("Editor font size"))
        font_row.set_subtitle(_("Changes the font size used in the editor"))
        font_row.set_value(self.win.config.get("editor_font_size", 10))
        font_row.connect("notify::value", self.on_editor_font_size_changed)
        editor_group.add(font_row)

        width_row = Adw.SpinRow.new_with_range(0, 400, 1)
        width_row.set_title(_("Content width"))
        width_row.set_subtitle(_("Controls the comfortable reading width. 0 disables the limit"))
        width_row.set_value(self.win.config.get("editor_content_width", 0))
        width_row.connect("notify::value", self.on_editor_width_changed)
        editor_group.add(width_row)

        focus_row = Adw.SwitchRow()
        focus_row.set_title(_("Focus mode"))
        focus_row.set_subtitle(_("Hides most controls while writing"))
        focus_row.set_active(self.win.config.get("focus_mode", False))
        focus_row.connect("notify::active", self.on_focus_mode_changed)
        editor_group.add(focus_row)

        return editor_group

    def create_autosave_preferences(self):
        autosave_group = Adw.PreferencesGroup()
        autosave_group.set_title(_("Recovery"))

        autosave_row = Adw.SpinRow.new_with_range(5, 120, 5)
        autosave_row.set_title(_("Auto-save interval"))
        autosave_row.set_subtitle(_("Saves recovery data every N seconds"))
        autosave_row.set_value(self.win.config.get("auto_save_interval", 10))
        autosave_row.connect("notify::value", self.on_auto_save_interval_changed)
        autosave_group.add(autosave_row)

        restore_row = Adw.SwitchRow()
        restore_row.set_title(_("Restore previous session"))
        restore_row.set_subtitle(_("Restores the last recovery file on startup"))
        restore_row.set_active(self.win.config.get("auto_restore_session", True))
        restore_row.connect("notify::active", self.on_restore_session_changed)
        autosave_group.add(restore_row)

        return autosave_group

    def create_render_preferences(self):
        render_group = Adw.PreferencesGroup()
        render_group.set_title(_("Render style"))

        style_row = Adw.ComboRow()
        style_row.set_title(_("Preview style"))
        style_row.set_subtitle(_("Changes the appearance of rendered content"))
        
        style_model = Gtk.StringList()
        style_options = [
            _("Default"),
            _("Slate"),
            _("Ivory"),
            _("Nocturne"),
            _("Ember"),
            _("Splendor"),
            _("Modest"),
            _("Retro"),
            _("Air")
        ]
        
        for option in style_options:
            style_model.append(option)
        
        style_row.set_model(style_model)

        current_style = self.win.config.get("render_style", "default")
        style_codes = RendererFactory.get_available_styles()
        
        if current_style in style_codes:
            style_row.set_selected(style_codes.index(current_style))
        else:
            style_row.set_selected(0)

        style_row.connect("notify::selected", self.on_render_style_changed)
        render_group.add(style_row)
        
        return render_group

    def on_render_style_changed(self, combo_row, param):
        selected = combo_row.get_selected()
        style_codes = RendererFactory.get_available_styles()
        
        if selected < len(style_codes):
            style_code = style_codes[selected]
            self.win.config.set("render_style", style_code)
            self.win.apply_render_style()

    def on_language_row_changed(self, combo_row, param):
        selected = combo_row.get_selected()
        available_languages = get_available_languages()
        
        if selected < len(available_languages):
            language_code = available_languages[selected][0]
            action = self.lookup_action("language")
            if action:
                action.activate(GLib.Variant("s", language_code))

    def on_color_scheme_changed(self, combo_row, param):
        selected = combo_row.get_selected()
        if selected < len(COLOR_SCHEMES):
            self.win.change_color_scheme(COLOR_SCHEMES[selected])

    def on_editor_font_size_changed(self, spin_row, _param):
        value = int(spin_row.get_value())
        self.win.config.set("editor_font_size", value)
        self.win.apply_editor_preferences()

    def on_editor_width_changed(self, spin_row, _param):
        value = int(spin_row.get_value())
        self.win.config.set("editor_content_width", value)
        self.win.apply_editor_preferences()

    def on_focus_mode_changed(self, switch_row, _param):
        self.win.set_focus_mode(switch_row.get_active())
        self.win.config.set("focus_mode", switch_row.get_active())

    def on_auto_save_interval_changed(self, spin_row, _param):
        value = int(spin_row.get_value())
        self.win.config.set("auto_save_interval", value)
        self.win.configure_auto_save()

    def on_restore_session_changed(self, switch_row, _param):
        self.win.config.set("auto_restore_session", switch_row.get_active())

    @staticmethod
    def _make_filter(name, mime_type, suffix):
        file_filter = Gtk.FileFilter()
        file_filter.set_name(name)
        file_filter.add_mime_type(mime_type)
        file_filter.add_suffix(suffix)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)
        return filters, file_filter

    @staticmethod
    def _finish_save(dialog, result, context):
        """Return the chosen file, or None when the user dismissed the dialog."""
        try:
            return dialog.save_finish(result)
        except GLib.Error as error:
            if not error.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED):
                print(f"Error in {context} dialog: {error.message}")
            return None

    def on_export_html(self, action, parameter):
        if not hasattr(self, "win") or not hasattr(self.win, "text_buffer"):
            return

        dialog = Gtk.FileDialog()
        dialog.set_title(_("Export as HTML"))
        dialog.set_initial_name("document.html")
        filters, default_filter = self._make_filter(_("HTML files"), "text/html", "html")
        dialog.set_filters(filters)
        dialog.set_default_filter(default_filter)
        dialog.save(self.win, None, self.on_export_html_response)

    def on_export_html_response(self, dialog, result):
        file = self._finish_save(dialog, result, "HTML export")
        if not file:
            return

        title = "Markdown Document"
        if self.win.current_file:
            title = self.win.current_file.rsplit("/", 1)[-1]
        text = self.win.text_buffer.get_text(
            self.win.text_buffer.get_start_iter(),
            self.win.text_buffer.get_end_iter(),
            False,
        )
        try:
            ExportService.export_html(
                file.get_path(),
                text,
                title=title,
                render_style=self.win.config.get("render_style", "default"),
            )
            self._toast(_("Exported as HTML"))
        except Exception as exc:
            print(f"Error exporting HTML: {exc}")
            self._toast(_("Could not export as HTML"))

    def on_export_pdf(self, action, parameter):
        if not hasattr(self, "win") or not hasattr(self.win, "text_buffer"):
            return

        dialog = Gtk.FileDialog()
        dialog.set_title(_("Export as PDF"))
        dialog.set_initial_name("document.pdf")
        filters, default_filter = self._make_filter(_("PDF files"), "application/pdf", "pdf")
        dialog.set_filters(filters)
        dialog.set_default_filter(default_filter)
        dialog.save(self.win, None, self.on_export_pdf_response)

    def on_export_pdf_response(self, dialog, result):
        file = self._finish_save(dialog, result, "PDF export")
        if file:
            self.export_preview_to_pdf(file)

    def prepare_preview_webview_for_printing(self, callback):
        if not hasattr(self, "win") or not hasattr(self.win, "text_buffer"):
            return
        if not hasattr(self.win, "preview_webview"):
            return

        text = self.win.text_buffer.get_text(
            self.win.text_buffer.get_start_iter(),
            self.win.text_buffer.get_end_iter(),
            False,
        )
        self.win.render_preview(text)

        webview = self.win.preview_webview

        def on_load_changed(view, load_event):
            if load_event != WebKit.LoadEvent.FINISHED:
                return
            if hasattr(self, "_pending_preview_load_handler") and self._pending_preview_load_handler:
                view.disconnect(self._pending_preview_load_handler)
                self._pending_preview_load_handler = None
            callback(view)

        if hasattr(self, "_pending_preview_load_handler") and self._pending_preview_load_handler:
            webview.disconnect(self._pending_preview_load_handler)
            self._pending_preview_load_handler = None

        if not webview.is_loading():
            callback(webview)
            return

        self._pending_preview_load_handler = webview.connect("load-changed", on_load_changed)

    def export_preview_to_pdf(self, file):
        if not WEBKIT_AVAILABLE:
            self._toast(_("PDF export needs WebKitGTK, which is not available"))
            return

        def run_export(webview):
            try:
                output_uri = file.get_uri() if hasattr(file, "get_uri") else Gio.File.new_for_path(file.get_path()).get_uri()
                print_settings = Gtk.PrintSettings()
                print_settings.set(Gtk.PRINT_SETTINGS_OUTPUT_URI, output_uri)
                print_settings.set(Gtk.PRINT_SETTINGS_OUTPUT_FILE_FORMAT, "pdf")
                print_settings.set(Gtk.PRINT_SETTINGS_PRINTER, "Print to File")

                print_operation = WebKit.PrintOperation.new(webview)
                print_operation.set_print_settings(print_settings)
                print_operation.print_()
                print_operation.run_dispose()
                self._toast(_("Exported as PDF"))
            except Exception as e:
                print(f"Error exporting PDF: {e}")
                self._toast(_("Could not export as PDF"))

        self.prepare_preview_webview_for_printing(run_export)

    def _syntax_reference(self):
        """Grouped the way the keyboard shortcuts dialog groups accelerators.

        Built here, with the literals inline, so xgettext can extract them: a
        module-level table translated through `_(variable)` would look
        translatable but never reach the catalogues.
        """
        return [
            (_("Text"), [
                (_("Bold"), "**text**"),
                (_("Italic"), "*text*"),
                (_("Strikethrough"), "~~text~~"),
                (_("Inline code"), "`code`"),
            ]),
            (_("Headings"), [
                (_("Heading 1"), "# Heading"),
                (_("Heading 2"), "## Heading"),
                (_("Heading 3"), "### Heading"),
                (_("Lower levels"), "#### … ######"),
            ]),
            (_("Lists"), [
                (_("Bullet list"), "- item"),
                (_("Numbered list"), "1. item"),
                (_("Task list"), "- [ ] item"),
            ]),
            (_("Blocks"), [
                (_("Quote"), "> quoted text"),
                (_("Code block"), "```"),
                (_("Horizontal line"), "---"),
            ]),
            (_("Links and media"), [
                (_("Insert link"), "[text](https://example.com)"),
                (_("Insert image"), "![alt](image.png)"),
                (_("Insert table"), "| A | B |"),
            ]),
        ]

    def on_syntax_help(self, action, parameter):
        if not hasattr(self, "win"):
            return

        dialog = Adw.Dialog(
            title=_("Markdown syntax"), content_width=560, content_height=620
        )

        page = Adw.PreferencesPage()
        for group_title, entries in self._syntax_reference():
            group = Adw.PreferencesGroup(title=group_title)
            for label, syntax in entries:
                row = Adw.ActionRow(title=label)
                snippet = Gtk.Label(label=syntax)
                snippet.add_css_class("monospace")
                snippet.add_css_class("dim-label")
                # Kept selectable so a snippet can still be copied out, which
                # the previous plain-text version allowed.
                snippet.set_selectable(True)
                snippet.set_valign(Gtk.Align.CENTER)
                row.add_suffix(snippet)
                group.add(row)
            page.add(group)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(page)
        dialog.set_child(toolbar)
        dialog.present(self.win)

    def on_shortcuts(self, action, parameter):
        if not hasattr(self, "win"):
            return

        # GtkShortcutsWindow and its Section/Group/Shortcut helpers are
        # deprecated since GTK 4.18; AdwShortcutsDialog replaces the lot.
        dialog = Adw.ShortcutsDialog()

        document = Adw.ShortcutsSection(title=_("Document"))
        for title, accelerator in [
            (_("New document"), "<Control>n"),
            (_("Open file"), "<Control>o"),
            (_("Save file"), "<Control>s"),
            (_("Print"), "<Control>p"),
        ]:
            document.add(Adw.ShortcutsItem(title=title, accelerator=accelerator))
        dialog.add(document)

        formatting = Adw.ShortcutsSection(title=_("Formatting"))
        for title, accelerator in [
            (_("Bold"), "<Control>b"),
            (_("Italic"), "<Control>i"),
            (_("Insert link"), "<Control>k"),
        ]:
            formatting.add(Adw.ShortcutsItem(title=title, accelerator=accelerator))
        dialog.add(formatting)

        general = Adw.ShortcutsSection(title=_("General"))
        for title, accelerator in [
            (_("Search"), "<Control>f"),
            (_("Hide search"), "Escape"),
            (_("Preferences"), "<Control>comma"),
            (_("Keyboard Shortcuts"), "<Control>question"),
        ]:
            general.add(Adw.ShortcutsItem(title=title, accelerator=accelerator))
        dialog.add(general)

        dialog.present(self.win)

    def on_about(self, action, parameter):
        if not Adw:
            print("Adwaita not available for About dialog")
            return
            
        about_dialog = Adw.AboutDialog()
        # The application's own icon, not a generic mime icon: there is no
        # "text-markdown-symbolic" in any icon theme, so GTK was falling back
        # to the full-colour text-markdown mime icon.
        about_dialog.set_application_icon(APP_ID)
        about_dialog.set_application_name(_("Markdown Editor"))
        about_dialog.set_version(build_version_string())
        about_dialog.set_developer_name(_("Developer"))
        about_dialog.set_copyright("© 2025")
        about_dialog.set_comments(
            _("A simple and powerful Markdown editor with real-time preview")
        )
        
        about_dialog.set_license_type(Gtk.License.GPL_3_0)
        about_dialog.set_developers([
            _("Main Developer"),
            _("Community Contributors")
        ])
        
        about_dialog.set_website("https://github.com/pabmartine/markdown-editor")
        about_dialog.set_issue_url("https://github.com/pabmartine/markdown-editor/issues")
        about_dialog.present(self.win)
    
    def on_activate(self, app):
        try:
            self.win = MarkdownEditorWindow(application=app)
            
            config = self.win.config
            width = config.get("window_width", 1000)
            height = config.get("window_height", 700)
            self.win.set_default_size(width, height)
            
            if hasattr(self.win, 'paned'):
                paned_position = config.get("paned_position", 500)
                def apply_paned_position():
                    if hasattr(self.win, 'paned'):
                        self.win.paned.set_position(paned_position)
                    return False
                
                GLib.timeout_add(100, apply_paned_position)

            if self.cli_args:
                apply_cli_options(self, self.cli_args)
            
            self.win.present()
            
        except Exception as e:
            print(f"Error activating application: {e}")
            traceback.print_exc()
