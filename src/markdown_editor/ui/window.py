import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

try:
    gi.require_version("WebKit", "6.0")
    from gi.repository import WebKit
    WEBKIT_AVAILABLE = True
except Exception:
    WebKit = None
    WEBKIT_AVAILABLE = False

from ..core.config import CONFIG_DIR, Config
from ..core.i18n import setup_locale, translate as _
from ..services.document_service import DocumentService
from ..services.html_preview import HtmlPreviewService
from ..services.session_service import SessionService
from . import icons
from .styles import apply_custom_css
from .support.editor_actions import EditorActionsMixin
from .support.file_operations import FileOperationsMixin
from .support.scroll_sync import ScrollSyncMixin
from .support.search import SearchMixin


class MarkdownEditorWindow(
    ScrollSyncMixin,
    SearchMixin,
    FileOperationsMixin,
    EditorActionsMixin,
    Adw.ApplicationWindow,
):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.config = Config()
        self.current_file = None
        self.document_modified = False
        self.current_language = self.config.get("language", "auto")
        self.pending_after_save = None
        self.pending_close = False
        self.click_in_progress = False
        self.outline_visible = False
        self.auto_save_source_id = None
        self.focus_mode_enabled = False
        self.session_service = SessionService(CONFIG_DIR)
        self.html_preview_service = HtmlPreviewService()

        self.apply_render_style()
        self.set_title(_("Markdown Editor"))
        self.set_default_size(1000, 700)
        # The HIG asks apps to keep working down to 360x294 logical pixels.
        self.set_size_request(360, 294)
        self.apply_saved_config()
        self.setup_ui()
        self.setup_shortcuts()
        self.configure_auto_save()
        self.restore_previous_session_if_needed()
        self.connect("close-request", self.on_close)

    def apply_saved_config(self):
        saved_language = self.config.get("language", "auto")
        if saved_language != "auto":
            setup_locale(saved_language)
            self.current_language = saved_language

        self.apply_color_scheme(self.get_color_scheme())
        self.focus_mode_enabled = self.config.get("focus_mode", False)

    def configure_auto_save(self):
        if self.auto_save_source_id:
            GLib.source_remove(self.auto_save_source_id)
            self.auto_save_source_id = None

        interval = max(5, int(self.config.get("auto_save_interval", 10)))
        self.auto_save_source_id = GLib.timeout_add_seconds(interval, self.on_auto_save_timer)

    def on_auto_save_timer(self):
        try:
            self.auto_save_recovery()
        except Exception as exc:
            print(f"Error in auto-save timer: {exc}")
        return True

    def auto_save_recovery(self):
        if not hasattr(self, "text_buffer"):
            return

        text = self.text_buffer.get_text(
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter(),
            False,
        )
        self.session_service.save_recovery(text, self.current_file)
        self.config.set("last_session_dirty", bool(text.strip()) or self.document_modified)

    def restore_previous_session_if_needed(self):
        if not self.config.get("auto_restore_session", True):
            return
        if not self.config.get("last_session_dirty", False):
            return

        recovery = self.session_service.load_recovery()
        if not recovery or not recovery["text"]:
            return

        self.show_editor_state()
        self.text_buffer.set_text(recovery["text"])
        self.current_file = recovery["source"] or None
        self.document_modified = True
        if self.current_file:
            self.update_title()
        if hasattr(self, "doc_status_label"):
            self.doc_status_label.set_text(_("Recovered session"))
        if hasattr(self, "save_btn"):
            self.save_btn.set_sensitive(True)

    def change_language(self, language_code):
        setup_locale(language_code if language_code != "auto" else None)
        self.config.set("language", language_code)
        self.current_language = language_code
        self.recreate_ui()

    def recreate_ui(self):
        if self.current_file:
            filename = os.path.basename(self.current_file)
            self.set_title(f"{filename} - {_('Markdown Editor')}")
        else:
            self.set_title(_("Markdown Editor"))

        # get_titlebar() on an AdwApplicationWindow returns an internal
        # AdwGizmo, not this header bar (which lives inside the content box),
        # so the previous lookup never found the label and the title kept the
        # old language.
        if hasattr(self, "header_title_label"):
            self.header_title_label.set_label(_("Markdown Editor"))

        if hasattr(self, "new_btn"):
            self.new_btn.set_tooltip_text(_("New document"))
        if hasattr(self, "open_btn"):
            self.open_btn.set_tooltip_text(_("Open file"))
        if hasattr(self, "save_btn"):
            self.save_btn.set_tooltip_text(_("Save file"))
        if hasattr(self, "search_btn"):
            self.search_btn.set_tooltip_text(_("Search (Ctrl+F)"))
        if hasattr(self, "search_entry"):
            self.search_entry.set_placeholder_text(_("Search in document..."))
        if hasattr(self, "replace_entry"):
            self.replace_entry.set_placeholder_text(_("Replace with..."))

        if hasattr(self, "doc_status_label"):
            current_status = self.doc_status_label.get_text()
            if "Modified" in current_status or "Modificado" in current_status:
                self.doc_status_label.set_text(_("Modified"))
            elif "Saved" in current_status or "Guardado" in current_status:
                self.doc_status_label.set_text(_("Saved"))
            elif "Ready" in current_status or "Listo" in current_status:
                self.doc_status_label.set_text(_("Ready"))

        if hasattr(self, "text_buffer"):
            text = self.text_buffer.get_text(
                self.text_buffer.get_start_iter(),
                self.text_buffer.get_end_iter(),
                False,
            )
            self.update_detailed_stats(text)
        else:
            if hasattr(self, "lines_label"):
                self.lines_label.set_text(f"1 {_('lines')}")
            if hasattr(self, "words_label"):
                self.words_label.set_text(f"0 {_('words')}")
            if hasattr(self, "chars_label"):
                self.chars_label.set_text(f"0 {_('chars')}")
            if hasattr(self, "headers_label"):
                self.headers_label.set_text(f"0 {_('headers')}")
            if hasattr(self, "reading_time_label"):
                self.reading_time_label.set_text(f"1 {_('min read')}")
            if hasattr(self, "cursor_label"):
                self.cursor_label.set_text(f"{_('Line')} 1, {_('Col')} 1")

        if hasattr(self, "content_stack") and self.content_stack.get_visible_child_name() == "welcome":
            self.update_welcome_page_language()
        if hasattr(self, "refresh_recent_files_ui"):
            self.refresh_recent_files_ui()
        if hasattr(self, "update_outline"):
            self.update_outline(
                self.text_buffer.get_text(
                    self.text_buffer.get_start_iter(),
                    self.text_buffer.get_end_iter(),
                    False,
                ) if hasattr(self, "text_buffer") else ""
            )

    def update_welcome_page_language(self):
        if hasattr(self, "welcome_page"):
            self.welcome_page.set_title(_("Markdown Editor"))
            self.welcome_page.set_description(
                _("Create and edit Markdown documents with real-time preview")
            )
        if hasattr(self, "welcome_info"):
            self.welcome_info.set_text(
                _("You can also use Ctrl+N to create a new file or Ctrl+O to open an existing one")
            )
        self.recreate_welcome_cards()

    def recreate_welcome_cards(self):
        """Swap the two cards for freshly translated ones."""
        if not hasattr(self, "welcome_options"):
            return

        parent = self.welcome_options.get_parent()
        if parent is None:
            return

        replacement = self.create_welcome_options()
        parent.insert_child_after(replacement, self.welcome_options)
        parent.remove(self.welcome_options)
        self.welcome_options = replacement

    def get_color_scheme(self):
        """Stored colour scheme, migrating the old boolean setting."""
        scheme = self.config.get("color_scheme")
        if scheme in ("default", "light", "dark"):
            return scheme
        return "dark" if self.config.get("dark_theme", False) else "default"

    def apply_color_scheme(self, scheme):
        """Follow the system preference unless the user overrides it.

        The previous version mapped the switch's "off" position to
        FORCE_LIGHT, so the app actively overrode a dark desktop instead of
        following it.
        """
        Adw.StyleManager.get_default().set_color_scheme(
            {
                "light": Adw.ColorScheme.FORCE_LIGHT,
                "dark": Adw.ColorScheme.FORCE_DARK,
            }.get(scheme, Adw.ColorScheme.DEFAULT)
        )

    def change_color_scheme(self, scheme):
        self.apply_color_scheme(scheme)
        self.config.set("color_scheme", scheme)

    def setup_ui(self):
        # AdwToolbarView + AdwHeaderBar instead of a Gtk.HeaderBar packed into
        # a plain Gtk.Box: the toolbar view is what gives the top/bottom bar
        # behaviour and integrates with the window's titlebar area.
        header_bar = Adw.HeaderBar()
        self.header_title_label = Gtk.Label(label=_("Markdown Editor"))
        header_bar.set_title_widget(self.header_title_label)

        self.new_btn = Gtk.Button()
        self.new_btn.set_icon_name(icons.name("new"))
        self.new_btn.set_tooltip_text(_("New document"))
        self.new_btn.connect("clicked", self.on_new)
        header_bar.pack_start(self.new_btn)

        self.open_btn = Gtk.MenuButton()
        self.open_btn.set_icon_name(icons.name("open"))
        self.open_btn.set_tooltip_text(_("Open file"))
        self.open_menu = Gio.Menu()
        self.open_recent_menu = Gio.Menu()
        self.open_menu.append(_("Open file"), "win.open-file")
        self.open_menu.append_submenu(_("Open Recent"), self.open_recent_menu)
        self.open_menu.append(_("Close current file"), "win.close-file")
        self.open_btn.set_menu_model(self.open_menu)
        header_bar.pack_start(self.open_btn)

        self.save_btn = Gtk.Button()
        self.save_btn.set_icon_name(icons.name("save"))
        self.save_btn.set_tooltip_text(_("Save file"))
        self.save_btn.connect("clicked", self.on_save)
        self.save_btn.set_sensitive(False)
        header_bar.pack_start(self.save_btn)

        self.search_btn = Gtk.Button()
        self.search_btn.set_icon_name(icons.name("search"))
        self.search_btn.set_tooltip_text(_("Search (Ctrl+F)"))
        self.search_btn.connect("clicked", lambda _button: self.toggle_search())
        # Grouped with the other document actions on the left, leaving the
        # primary menu alone at the end.
        header_bar.pack_start(self.search_btn)

        self.setup_menu_button(header_bar)

        self.root_toolbar = Adw.ToolbarView()
        self.root_toolbar.add_top_bar(header_bar)

        # The search bar sits directly under the header bar, which is where the
        # HIG puts it; it used to be at the bottom of the editor area.
        self.search_bar = self.create_search_bar()
        self.root_toolbar.add_top_bar(self.search_bar)

        self.setup_main_layout(self.root_toolbar)

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.root_toolbar)
        self.set_content(self.toast_overlay)

        self.setup_breakpoints()
        self.update_recent_menu()
        self.apply_css()
        self.show_welcome_state()
        self.apply_editor_preferences()
        self.set_focus_mode(self.focus_mode_enabled)

    def setup_menu_button(self, header_bar):
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name(icons.name("menu"))
        self.menu_button.set_tooltip_text(_("Main Menu"))

        menu_model = Gio.Menu()
        document_section = Gio.Menu()
        document_section.append(_("Save as"), "win.save-as")
        document_section.append(_("Export as HTML"), "app.export_html")
        document_section.append(_("Export as PDF"), "app.export_pdf")
        document_section.append(_("Print..."), "app.print")
        menu_model.append_section(None, document_section)

        view_section = Gio.Menu()
        view_section.append(_("Toggle outline"), "win.toggle-outline")
        view_section.append(_("Toggle focus mode"), "win.toggle-focus")
        menu_model.append_section(None, view_section)

        app_section = Gio.Menu()
        app_section.append(_("Preferences"), "app.preferences")
        # These two actions were registered but reachable from nowhere.
        app_section.append(_("Markdown Syntax"), "app.syntax_help")
        app_section.append(_("Keyboard Shortcuts"), "app.shortcuts")
        app_section.append(_("About Markdown Editor"), "app.about")
        menu_model.append_section(None, app_section)
        self.menu_button.set_menu_model(menu_model)
        header_bar.pack_end(self.menu_button)

        open_action = Gio.SimpleAction.new("open-file", None)
        open_action.connect("activate", lambda _action, _param: self.on_open(None))
        self.add_action(open_action)

        save_as_action = Gio.SimpleAction.new("save-as", None)
        save_as_action.connect("activate", lambda _action, _param: self.save_as())
        self.add_action(save_as_action)

        toggle_outline_action = Gio.SimpleAction.new("toggle-outline", None)
        toggle_outline_action.connect("activate", lambda _action, _param: self.toggle_outline())
        self.add_action(toggle_outline_action)

        toggle_focus_action = Gio.SimpleAction.new("toggle-focus", None)
        toggle_focus_action.connect("activate", lambda _action, _param: self.toggle_focus_mode())
        self.add_action(toggle_focus_action)

        close_file_action = Gio.SimpleAction.new("close-file", None)
        close_file_action.connect("activate", lambda _action, _param: self.on_close_file(None))
        self.add_action(close_file_action)

    def install_recent_action(self, action_name, file_path):
        existing = self.lookup_action(action_name)
        if existing:
            self.remove_action(action_name)

        action = Gio.SimpleAction.new(action_name, None)
        action.connect("activate", lambda _action, _param, path=file_path: self.open_recent_file(path))
        self.add_action(action)

    def update_recent_menu(self):
        if not hasattr(self, "open_recent_menu"):
            return

        self.open_recent_menu.remove_all()
        recent_files = self.get_recent_files()
        if recent_files:
            for index, file_path in enumerate(recent_files[:5]):
                action_name = f"open-recent-{index}"
                self.install_recent_action(action_name, file_path)
                self.open_recent_menu.append(os.path.basename(file_path), f"win.{action_name}")
        else:
            if self.lookup_action("no-recent-files"):
                self.remove_action("no-recent-files")
            empty_action = Gio.SimpleAction.new("no-recent-files", None)
            empty_action.connect("activate", lambda _action, _param: None)
            self.add_action(empty_action)
            self.open_recent_menu.append(_("No recent files"), "win.no-recent-files")

    def setup_main_layout(self, toolbar_view):
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.content_stack.set_hexpand(True)
        self.content_stack.set_vexpand(True)

        self.welcome_page = self.create_welcome_page()
        self.content_stack.add_named(self.welcome_page, "welcome")

        self.editor_area = self.create_editor_area()
        self.content_stack.add_named(self.editor_area, "editor")

        toolbar_view.set_content(self.content_stack)

    def create_welcome_page(self):
        """AdwStatusPage, the documented pattern for a placeholder view.

        It supplies the icon, title, description and centring that were being
        hand-assembled, and stays legible when the window is narrow.
        """
        self.welcome_page = Adw.StatusPage()
        self.welcome_page.set_icon_name(icons.name("markdown"))
        self.welcome_page.set_title(_("Markdown Editor"))
        self.welcome_page.set_description(
            _("Create and edit Markdown documents with real-time preview")
        )

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        body.set_halign(Gtk.Align.CENTER)
        self.welcome_options = self.create_welcome_options()
        body.append(self.welcome_options)

        self.welcome_info = Gtk.Label()
        self.welcome_info.set_text(
            _("You can also use Ctrl+N to create a new file or Ctrl+O to open an existing one")
        )
        self.welcome_info.add_css_class("dim-label")
        self.welcome_info.set_wrap(True)
        self.welcome_info.set_justify(Gtk.Justification.CENTER)
        body.append(self.welcome_info)

        self.welcome_page.set_child(body)
        return self.welcome_page

    def refresh_recent_files_ui(self):
        recent_files = self.get_recent_files()
        self.update_recent_menu()

    def create_welcome_options(self):
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        options_box.set_spacing(30)
        options_box.set_halign(Gtk.Align.CENTER)
        options_box.append(
            self.create_welcome_card(
                "document-new-symbolic",
                _("New Document"),
                _("Create a new blank Markdown document"),
                _("Create New"),
                self.on_new_from_welcome,
            )
        )
        options_box.append(
            self.create_welcome_card(
                "document-open-symbolic",
                _("Open File"),
                _("Open an existing Markdown document"),
                _("Open File"),
                self.on_open_from_welcome,
                suggested=False,
            )
        )
        return options_box

    def create_welcome_card(self, icon_name, title, description, button_text, callback, suggested=True):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("welcome-card")
        card.set_size_request(280, 200)

        icon = Gtk.Image()
        icon.set_from_icon_name(icon_name)
        icon.set_pixel_size(64)
        icon.add_css_class("dim-label")
        card.append(icon)

        label = Gtk.Label()
        label.set_markup(f"<span size='large' weight='bold'>{title}</span>")
        label.set_margin_top(20)
        card.append(label)

        desc = Gtk.Label(label=description)
        desc.add_css_class("dim-label")
        desc.set_wrap(True)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_margin_top(10)
        card.append(desc)

        button = Gtk.Button(label=button_text)
        # The HIG allows a single suggested action per view, so only the first
        # card carries the accent.
        if suggested:
            button.add_css_class("suggested-action")
        button.add_css_class("pill")
        button.set_margin_top(20)
        button.connect("clicked", callback)
        card.append(button)
        return card

    def create_editor_area(self):
        # A nested toolbar view so the formatting toolbar and the status bar are
        # real top/bottom bars of the editor, and only exist in editor mode.
        editor_toolbar = Adw.ToolbarView()
        editor_toolbar.add_top_bar(self.create_toolbar())

        panels_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.create_main_panels(panels_box)
        editor_toolbar.set_content(panels_box)

        editor_toolbar.add_bottom_bar(self.create_status_bar())
        return editor_toolbar

    def create_toolbar(self):
        toolbar_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.toolbar_container = toolbar_container
        toolbar_container.add_css_class("toolbar")
        toolbar_container.set_margin_start(8)
        toolbar_container.set_margin_end(8)
        toolbar_container.set_margin_top(4)
        toolbar_container.set_margin_bottom(4)
        # The fifteen formatting buttons cannot all fit on a narrow window, so
        # they scroll horizontally instead of being clipped. Without
        # propagate-natural-width the scrolled window is free to shrink, which
        # is what lets the row give way before the view switcher does.
        format_scroll = Gtk.ScrolledWindow()
        format_scroll.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.NEVER)
        format_scroll.set_hexpand(True)
        format_scroll.set_child(self.create_format_buttons())
        toolbar_container.append(format_scroll)

        toolbar_container.append(self.create_view_buttons())
        return toolbar_container

    def create_format_buttons(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        toolbar.set_spacing(0)
        toolbar.set_halign(Gtk.Align.START)

        def create_icon_button(icon_key, tooltip, callback=None):
            btn = Gtk.Button()
            btn.set_icon_name(icons.name(icon_key))
            btn.set_tooltip_text(tooltip)
            btn.add_css_class("flat")
            btn.add_css_class("super-compact-btn")
            btn.set_size_request(18, 18)
            if callback:
                btn.connect("clicked", callback)
            return btn

        def add_separator():
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_start(6)
            sep.set_margin_end(6)
            sep.add_css_class("group-separator")
            toolbar.append(sep)

        toolbar.append(create_icon_button("bold", _("Bold (Ctrl+B)"), lambda _x: self.insert_format("**", "**")))
        toolbar.append(create_icon_button("italic", _("Italic (Ctrl+I)"), lambda _x: self.insert_format("*", "*")))
        toolbar.append(create_icon_button("strikethrough", _("Strikethrough"), lambda _x: self.insert_format("~~", "~~")))
        toolbar.append(self.create_headers_menu())
        add_separator()
        toolbar.append(create_icon_button("list-bullet", _("Bullet list"), lambda _x: self.insert_list_item("unordered")))
        toolbar.append(create_icon_button("list-ordered", _("Numbered list"), lambda _x: self.insert_list_item("ordered")))
        toolbar.append(create_icon_button("list-task", _("Task list"), lambda _x: self.insert_list_item("task")))
        toolbar.append(create_icon_button("quote", _("Quote"), lambda _x: self.insert_format("> ", "")))
        add_separator()
        toolbar.append(create_icon_button("code-inline", _("Inline code"), lambda _x: self.insert_format("`", "`")))
        toolbar.append(create_icon_button("code-block", _("Code block"), lambda _x: self.insert_format("```\n", "\n```")))
        add_separator()
        toolbar.append(create_icon_button("link", _("Insert link (Ctrl+K)"), self.insert_link_markup))
        toolbar.append(create_icon_button("image", _("Insert image"), self.insert_image_markup))
        toolbar.append(create_icon_button("table", _("Insert table"), self.insert_table))
        add_separator()
        toolbar.append(create_icon_button("rule", _("Horizontal line"), lambda _x: self.insert_format("\n---\n", "")))
        return toolbar

    def create_headers_menu(self):
        headers_button = Gtk.MenuButton()
        headers_button.set_icon_name(icons.name("heading"))
        headers_button.set_tooltip_text(_("Select header"))
        headers_button.add_css_class("super-compact-btn")
        headers_button.set_size_request(18, 18)

        popover = Gtk.Popover()
        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        popover_box.set_spacing(0)
        for text, prefix, level in [
            ("H1", "# ", 1),
            ("H2", "## ", 2),
            ("H3", "### ", 3),
            ("H4", "#### ", 4),
            ("H5", "##### ", 5),
            ("H6", "###### ", 6),
        ]:
            btn = Gtk.Button()
            btn.add_css_class("header-preview-btn")
            btn.add_css_class(f"header-preview-btn-h{level}")
            btn.set_size_request(-1, 28)
            label = Gtk.Label(label=text)
            label.set_xalign(0.0)
            label.add_css_class("header-preview-label")
            label.add_css_class(f"header-preview-label-h{level}")
            btn.set_child(label)
            btn.connect("clicked", lambda _x, p=prefix: (self.insert_format(p, ""), popover.popdown()))
            popover_box.append(btn)
        popover.set_child(popover_box)
        headers_button.set_popover(popover)
        return headers_button

    def create_view_buttons(self):
        view_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        view_buttons_box.set_spacing(0)

        def create_view_button(icon_key, tooltip):
            btn = Gtk.Button()
            btn.set_icon_name(icons.name(icon_key))
            btn.set_tooltip_text(tooltip)
            btn.add_css_class("flat")
            btn.add_css_class("super-compact-btn")
            btn.set_size_request(18, 18)
            return btn

        self.editor_view_btn = create_view_button("view-editor", _("Editor only"))
        self.editor_view_btn.connect("clicked", lambda _x: self.set_view_mode("editor"))
        view_buttons_box.append(self.editor_view_btn)

        self.split_view_btn = create_view_button("view-split", _("Split view"))
        self.split_view_btn.connect("clicked", lambda _x: self.set_view_mode("split"))
        self.split_view_btn.add_css_class("view-btn-active")
        view_buttons_box.append(self.split_view_btn)

        self.preview_view_btn = create_view_button("view-preview", _("Preview only"))
        self.preview_view_btn.connect("clicked", lambda _x: self.set_view_mode("preview"))
        view_buttons_box.append(self.preview_view_btn)
        return view_buttons_box

    def create_main_panels(self, main_box):
        self.outline_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.outline_paned.set_vexpand(True)
        self.outline_paned.set_hexpand(True)
        self.outline_paned.set_start_child(self.create_outline_panel())

        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_vexpand(True)
        self.paned.set_hexpand(True)
        self.current_view_mode = "split"
        self.create_editor_panel()
        self.create_preview_panel()
        self.setup_scroll_sync()
        self.paned.set_position(500)
        self.outline_paned.set_end_child(self.paned)
        self.outline_paned.set_position(220)
        main_box.append(self.outline_paned)
        self.outline_panel.set_visible(False)

    def create_outline_panel(self):
        outline_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outline_container.set_vexpand(True)
        outline_container.set_hexpand(False)
        outline_container.set_size_request(220, -1)
        outline_container.set_margin_start(8)
        outline_container.set_margin_end(4)
        outline_container.set_margin_top(6)
        outline_container.set_margin_bottom(6)
        self.outline_panel = outline_container

        title = Gtk.Label()
        title.set_markup(f"<span weight='bold'>{_('Outline')}</span>")
        title.set_halign(Gtk.Align.CENTER)
        title.set_justify(Gtk.Justification.CENTER)
        outline_container.append(title)

        self.outline_list = Gtk.ListBox()
        self.outline_list.set_selection_mode(Gtk.SelectionMode.NONE)

        outline_scroll = Gtk.ScrolledWindow()
        outline_scroll.set_min_content_width(220)
        outline_scroll.set_vexpand(True)
        outline_scroll.set_hexpand(True)
        outline_scroll.set_child(self.outline_list)
        outline_container.append(outline_scroll)
        return outline_container

    def toggle_outline(self):
        if not hasattr(self, "outline_panel"):
            return
        self.outline_visible = not self.outline_visible
        self.outline_panel.set_visible(self.outline_visible)
        if hasattr(self, "outline_toggle_btn"):
            if self.outline_visible:
                self.outline_toggle_btn.add_css_class("view-btn-active")
                if hasattr(self, "outline_paned"):
                    self.outline_paned.set_position(max(180, self.outline_paned.get_position()))
            else:
                self.outline_toggle_btn.remove_css_class("view-btn-active")

    def update_outline(self, text):
        if not hasattr(self, "outline_list"):
            return

        child = self.outline_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.outline_list.remove(child)
            child = next_child

        headers = DocumentService.extract_headers(text)
        if not headers:
            row = Gtk.Label(label=_("No headings"))
            row.set_xalign(0)
            row.set_halign(Gtk.Align.FILL)
            row.set_hexpand(True)
            row.set_margin_start(12)
            row.set_margin_end(6)
            row.add_css_class("dim-label")
            self.outline_list.append(row)
            self.outline_buttons = []
            return

        self.outline_buttons = []
        for header in headers:
            label = Gtk.Label(label=header.title)
            label.set_xalign(0)
            button = Gtk.Button()
            button.add_css_class("flat")
            button.set_halign(Gtk.Align.FILL)
            button.set_tooltip_text(f"{_('Line')} {header.line}")
            button.set_margin_start((header.level - 1) * 12)
            button.set_child(label)
            button.connect("clicked", lambda _btn, line=header.line: self.scroll_to_line(line))
            self.outline_list.append(button)
            self.outline_buttons.append((header.line, button))

        self.refresh_active_outline_from_cursor()

    def scroll_to_line(self, line_number):
        if not hasattr(self, "text_buffer") or not hasattr(self, "text_view"):
            return

        end_iter = self.text_buffer.get_end_iter()
        total_lines = max(1, end_iter.get_line() + 1)
        target_line = max(0, min(line_number - 1, total_lines - 1))
        line_result = self.text_buffer.get_iter_at_line(target_line)
        target_iter = line_result.iter if hasattr(line_result, "iter") else line_result[1]
        self.text_buffer.place_cursor(target_iter)
        self.text_view.scroll_to_iter(target_iter, 0.1, False, 0.0, 0.0)

        if hasattr(self, "preview_vadj"):
            ratio = target_line / max(1, total_lines - 1)
            preview_max = self.preview_vadj.get_upper() - self.preview_vadj.get_page_size()
            if preview_max > 0:
                self.sync_scroll_enabled = False
                try:
                    self.preview_vadj.set_value(ratio * preview_max)
                finally:
                    self.sync_scroll_enabled = True

        self.text_view.grab_focus()

    def create_editor_panel(self):
        self.editor_scroll = Gtk.ScrolledWindow()
        self.editor_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.text_view = Gtk.TextView()
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_left_margin(20)
        self.text_view.set_right_margin(20)
        self.text_view.set_top_margin(15)
        self.text_view.set_bottom_margin(15)
        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.connect("changed", self.on_text_changed)
        self.text_buffer.connect("mark-set", self.on_text_buffer_mark_set)
        self.setup_search_tags()
        self.setup_editor_events()
        self.setup_drop_targets()
        self.editor_scroll.set_child(self.text_view)
        self.paned.set_start_child(self.editor_scroll)

    def on_text_buffer_mark_set(self, _buffer, _iter, mark):
        if mark and mark.get_name() == "insert":
            self.refresh_active_outline_from_cursor()

    def refresh_active_outline_from_cursor(self):
        if not hasattr(self, "text_buffer") or not hasattr(self, "outline_buttons"):
            return

        insert_mark = self.text_buffer.get_insert()
        current_iter = self.text_buffer.get_iter_at_mark(insert_mark)
        current_line = current_iter.get_line() + 1

        for header_line, button in self.outline_buttons:
            if header_line == current_line:
                pass

        current_header = DocumentService.find_current_header(
            self.text_buffer.get_text(
                self.text_buffer.get_start_iter(),
                self.text_buffer.get_end_iter(),
                False,
            ),
            current_line,
        )
        active_line = current_header.line if current_header else None

        for header_line, button in self.outline_buttons:
            if header_line == active_line:
                button.add_css_class("outline-active")
            else:
                button.remove_css_class("outline-active")

    def setup_drop_targets(self):
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_files_dropped)
        self.text_view.add_controller(drop_target)

    def on_files_dropped(self, _target, file_list, _x, _y):
        files = list(file_list.get_files()) if file_list else []
        paths = [gio_file.get_path() for gio_file in files if gio_file.get_path()]
        if not paths:
            return False

        image_paths = [path for path in paths if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"))]
        markdown_paths = [path for path in paths if path.lower().endswith((".md", ".markdown", ".mdown", ".mkd", ".txt"))]

        if markdown_paths:
            self.open_recent_file(markdown_paths[0])

        if image_paths and hasattr(self, "text_buffer"):
            snippets = []
            for path in image_paths:
                display_path = path
                if self.current_file:
                    try:
                        display_path = os.path.relpath(path, os.path.dirname(self.current_file))
                    except ValueError:
                        display_path = path
                snippets.append(f"![{os.path.basename(path)}]({display_path})")
            prefix = "\n" if markdown_paths else ""
            self.text_buffer.insert_at_cursor(prefix + "\n".join(snippets))

        return True

    def create_preview_panel(self):
        self.preview_scroll = Gtk.ScrolledWindow()
        self.preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_click = Gtk.GestureClick()
        preview_click.connect("pressed", self.on_preview_clicked)

        if WEBKIT_AVAILABLE:
            self.preview_webview = WebKit.WebView()
            self.preview_webview.set_hexpand(True)
            self.preview_webview.set_vexpand(True)
            self.preview_webview.connect("decide-policy", self.on_preview_decide_policy)
            self.preview_webview.add_controller(preview_click)
            self.preview_scroll.set_child(self.preview_webview)
        else:
            fallback = Gtk.Label(label=_("Preview requires WebKitGTK for GTK4 (WebKit 6.0)"))
            fallback.add_css_class("dim-label")
            fallback.set_margin_top(24)
            fallback.set_margin_bottom(24)
            fallback.set_margin_start(24)
            fallback.set_margin_end(24)
            self.preview_scroll.set_child(fallback)

        self.paned.set_end_child(self.preview_scroll)

    def on_preview_decide_policy(self, _webview, decision, decision_type):
        if not WEBKIT_AVAILABLE or decision_type != WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            return False

        try:
            navigation_action = decision.get_navigation_action()
            if not navigation_action:
                return False

            if navigation_action.get_navigation_type() != WebKit.NavigationType.LINK_CLICKED:
                return False

            request = navigation_action.get_request()
            uri = request.get_uri() if request else None
            if not uri or uri == "about:blank":
                return False

            if getattr(self, "preview_base_uri", None) and uri.startswith(f"{self.preview_base_uri}#"):
                return False

            Gio.AppInfo.launch_default_for_uri(uri, None)
            decision.ignore()
            return True
        except Exception as exc:
            print(f"Error opening preview link: {exc}")
            return False

    def create_status_bar(self):
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.status_box = status_box
        status_box.add_css_class("toolbar")
        status_box.set_spacing(8)
        status_box.set_margin_start(15)
        status_box.set_margin_end(15)
        status_box.set_margin_top(3)
        status_box.set_margin_bottom(3)

        def metric(text):
            label = Gtk.Label(label=text)
            label.add_css_class("dim-label")
            # Tabular figures, so the numbers do not jitter as they change.
            label.add_css_class("numeric")
            return label

        def separator():
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            return sep

        self.doc_status_label = Gtk.Label(label=_("Ready"))
        self.doc_status_label.add_css_class("dim-label")
        status_box.append(self.doc_status_label)

        status_box.append(separator())
        self.lines_label = metric(f"1 {_('lines')}")
        status_box.append(self.lines_label)
        status_box.append(separator())
        self.words_label = metric(f"0 {_('words')}")
        status_box.append(self.words_label)

        # Secondary metrics live in their own box so a breakpoint can drop them
        # when the window gets too narrow to hold the whole row.
        extra = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status_extra_box = extra
        extra.append(separator())
        self.chars_label = metric(f"0 {_('chars')}")
        extra.append(self.chars_label)
        extra.append(separator())
        self.headers_label = metric(f"0 {_('headers')}")
        extra.append(self.headers_label)
        extra.append(separator())
        self.reading_time_label = metric(f"1 {_('min read')}")
        extra.append(self.reading_time_label)
        extra.append(separator())
        self.size_label = metric("0 B")
        extra.append(self.size_label)
        status_box.append(extra)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        status_box.append(spacer)

        # Cursor position and file type also go in their own box: with these
        # plus the metrics above, the status bar alone demanded ~472px, which
        # kept the whole window from ever getting narrow.
        trailing = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status_trailing_box = trailing
        self.cursor_label = metric(f"{_('Line')} 1, {_('Col')} 1")
        trailing.append(self.cursor_label)
        trailing.append(separator())
        self.filetype_label = Gtk.Label(label="Markdown")
        self.filetype_label.add_css_class("dim-label")
        trailing.append(self.filetype_label)
        status_box.append(trailing)
        return status_box

    def show_welcome_state(self):
        self.content_stack.set_visible_child_name("welcome")
        self.set_title(_("Markdown Editor"))
        for btn_name in ["new_btn", "open_btn", "save_btn", "search_btn", "menu_button"]:
            if hasattr(self, btn_name):
                getattr(self, btn_name).set_visible(False)
        print_action = self.get_application().lookup_action("print")
        if print_action:
            print_action.set_enabled(False)

    def show_editor_state(self):
        self.content_stack.set_visible_child_name("editor")
        for btn_name in ["new_btn", "open_btn", "save_btn", "search_btn", "menu_button"]:
            if hasattr(self, btn_name):
                getattr(self, btn_name).set_visible(True)
        print_action = self.get_application().lookup_action("print")
        if print_action:
            print_action.set_enabled(True)

    def show_toast(self, toast):
        """Transient feedback. Accepts a string or a ready-made AdwToast."""
        if isinstance(toast, str):
            toast = Adw.Toast.new(toast)
        if hasattr(self, "toast_overlay"):
            self.toast_overlay.add_toast(toast)

    def apply_css(self):
        apply_custom_css()

    def apply_editor_preferences(self):
        font_size = max(1, int(self.config.get("editor_font_size", 10)))
        content_width = max(0, int(self.config.get("editor_content_width", 0)))
        side_margin = 20 if content_width == 0 else max(20, min(300, content_width * 3))

        if hasattr(self, "text_view"):
            self.text_view.set_pixels_above_lines(max(0, font_size // 8))
            self.text_view.set_pixels_below_lines(max(0, font_size // 8))
            self.text_view.set_left_margin(side_margin)
            self.text_view.set_right_margin(side_margin)
            self.text_view.add_css_class("editor-custom")
            # Replace the previous provider: this runs on every font-size
            # change, and adding without removing stacked them up.
            display = Gdk.Display.get_default()
            if display is not None:
                if getattr(self, "_editor_font_provider", None) is not None:
                    Gtk.StyleContext.remove_provider_for_display(
                        display, self._editor_font_provider
                    )
                self._editor_font_provider = Gtk.CssProvider()
                self._editor_font_provider.load_from_string(
                    f"textview.editor-custom {{ font-size: {font_size}pt; }}"
                )
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    self._editor_font_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
                )

        self.preview_width_chars = 0 if content_width == 0 else max(20, min(400, content_width))
        if hasattr(self, "text_buffer"):
            self.update_preview_with_new_style()

    def toggle_focus_mode(self):
        self.set_focus_mode(not self.focus_mode_enabled)
        self.config.set("focus_mode", self.focus_mode_enabled)

    def set_focus_mode(self, enabled):
        self.focus_mode_enabled = enabled
        for btn_name in ["new_btn", "open_btn", "save_btn", "search_btn"]:
            if hasattr(self, btn_name):
                getattr(self, btn_name).set_visible(not enabled if self.content_stack.get_visible_child_name() == "editor" else False)
        if hasattr(self, "menu_button"):
            self.menu_button.set_visible(self.content_stack.get_visible_child_name() == "editor")
        if hasattr(self, "outline_panel"):
            self.outline_panel.set_visible(self.outline_visible and not enabled)
        if hasattr(self, "search_bar"):
            self.search_bar.set_visible(not enabled)
        if hasattr(self, "toolbar_container"):
            self.toolbar_container.set_visible(not enabled)
        if hasattr(self, "status_box"):
            self.status_box.set_visible(not enabled)

    def setup_breakpoints(self):
        """Collapse progressively as the window narrows.

        Only one breakpoint applies at a time: AdwBreakpointBin uses the last
        added one whose condition matches, so the conditions here are made
        mutually exclusive and the narrower one repeats the setters of the
        wider one. `sp` units follow the user's text scaling factor.
        """
        # Medium: the window still holds the panes, but not every metric.
        medium = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("min-width: 701sp and max-width: 900sp")
        )
        if hasattr(self, "status_extra_box"):
            medium.add_setter(self.status_extra_box, "visible", False)
        self.add_breakpoint(medium)

        # Narrow: drop the remaining metrics too and show a single pane.
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 700sp"))
        if hasattr(self, "status_extra_box"):
            narrow.add_setter(self.status_extra_box, "visible", False)
        if hasattr(self, "status_trailing_box"):
            narrow.add_setter(self.status_trailing_box, "visible", False)
        narrow.connect("apply", self._on_narrow_applied)
        narrow.connect("unapply", self._on_narrow_unapplied)
        self.add_breakpoint(narrow)

    def _on_narrow_applied(self, _breakpoint):
        self._view_mode_before_narrow = getattr(self, "current_view_mode", "split")
        self._outline_before_narrow = self.outline_visible
        if self.outline_visible:
            self.toggle_outline()
        if self.current_view_mode == "split":
            self.set_view_mode("editor")
        if hasattr(self, "split_view_btn"):
            self.split_view_btn.set_sensitive(False)

    def _on_narrow_unapplied(self, _breakpoint):
        if hasattr(self, "split_view_btn"):
            self.split_view_btn.set_sensitive(True)
        if getattr(self, "_view_mode_before_narrow", None):
            self.set_view_mode(self._view_mode_before_narrow)
            self._view_mode_before_narrow = None
        if getattr(self, "_outline_before_narrow", False) and not self.outline_visible:
            self.toggle_outline()
            self._outline_before_narrow = False

    def setup_shortcuts(self):
        controller = Gtk.ShortcutController()
        shortcuts = [
            ("<Control>b", lambda *args: self.insert_format("**", "**")),
            ("<Control>i", lambda *args: self.insert_format("*", "*")),
            ("<Control>k", lambda *args: self.insert_format("[", "](https://)")),
            ("<Control>n", lambda *args: self.on_new(None)),
            ("<Control>o", lambda *args: self.on_open(None)),
            ("<Control>s", lambda *args: self.on_save(None)),
            ("<Control>f", lambda *args: self.toggle_search()),
            ("<Control>h", lambda *args: self.toggle_search()),
            ("Escape", lambda *args: self.hide_search()),
        ]
        for trigger_string, callback in shortcuts:
            shortcut = Gtk.Shortcut()
            shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string(trigger_string))
            shortcut.set_action(Gtk.CallbackAction.new(callback))
            controller.add_shortcut(shortcut)
        self.add_controller(controller)

    def apply_render_style(self):
        self.apply_css()
        if hasattr(self, "text_buffer"):
            self.update_preview_with_new_style()

    def update_preview_with_new_style(self):
        if not hasattr(self, "text_buffer"):
            return
        text = self.text_buffer.get_text(
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter(),
            False,
        )
        self.render_preview(text)

    def render_preview(self, text):
        if not hasattr(self, "preview_webview"):
            return

        title = os.path.basename(self.current_file) if self.current_file else _("Markdown Editor")
        self.preview_base_uri = self.html_preview_service.build_base_uri(self.current_file)
        document = self.html_preview_service.render_document(
            text,
            title=title,
            render_style=self.config.get("render_style", "default"),
            max_width_chars=getattr(self, "preview_width_chars", 0),
        )
        self.preview_webview.load_html(document, self.preview_base_uri)

    def on_close(self, window):
        if self.pending_close:
            self.pending_close = False
        elif self.has_unsaved_changes():
            self.confirm_discard_changes(self.request_close)
            return True

        if hasattr(self, "paned"):
            self.config.set("paned_position", self.paned.get_position())

        if self.document_modified:
            self.auto_save_recovery()
        else:
            self.session_service.clear_recovery()
            self.config.set("last_session_dirty", False)

        width, height = self.get_default_size()
        self.config.set("window_width", width)
        self.config.set("window_height", height)
        return False
