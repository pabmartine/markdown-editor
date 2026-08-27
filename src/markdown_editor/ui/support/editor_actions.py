import os
import re

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from ...core.i18n import translate as _
from ...services.document_service import DocumentService


def _form_dialog(title, content, on_accept, parent, accept_label):
    """An AdwDialog with Cancel/accept in its header bar.

    Replaces Gtk.Dialog (deprecated in GTK 4.10) and puts the actions in the
    header bar, which is where the HIG asks for them.
    """
    dialog = Adw.Dialog(title=title, content_width=420)

    header = Adw.HeaderBar()
    header.set_show_start_title_buttons(False)
    header.set_show_end_title_buttons(False)

    cancel_button = Gtk.Button(label=_("Cancel"))
    cancel_button.connect("clicked", lambda _b: dialog.close())
    header.pack_start(cancel_button)

    accept_button = Gtk.Button(label=accept_label)
    accept_button.add_css_class("suggested-action")

    def accept(_button):
        on_accept()
        dialog.close()

    accept_button.connect("clicked", accept)
    header.pack_end(accept_button)

    content.set_margin_start(12)
    content.set_margin_end(12)
    content.set_margin_top(12)
    content.set_margin_bottom(12)

    toolbar = Adw.ToolbarView()
    toolbar.add_top_bar(header)
    toolbar.set_content(content)
    dialog.set_child(toolbar)
    dialog.set_default_widget(accept_button)
    dialog.present(parent)
    return dialog


class EditorActionsMixin:
    LIST_CONTINUATION_PATTERNS = [
        (re.compile(r'^(\s*)-\s+\[\s*\]\s*(.*)$'), "task"),
        (re.compile(r'^(\s*)-\s+\[[xX]\]\s*(.*)$'), "task"),
        (re.compile(r'^(\s*)(\d+)\.\s+(.*)$'), "ordered"),
        (re.compile(r'^(\s*)-\s+(.*)$'), "unordered_dash"),
        (re.compile(r'^(\s*)\*\s+(.*)$'), "unordered_star"),
        (re.compile(r'^(\s*)\+\s+(.*)$'), "unordered_plus"),
    ]

    def setup_editor_events(self):
        if not hasattr(self, 'text_view') or not Gtk:
            return
            
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.text_view.add_controller(key_controller)
        
        self.in_list_context = False
    
    def insert_format(self, prefix, suffix=""):
        if not hasattr(self, 'text_buffer'):
            return
            
        try:
            bounds = self.text_buffer.get_selection_bounds()
            
            if bounds:
                start, end = bounds
                selected_text = self.text_buffer.get_text(start, end, False)
                replacement = f"{prefix}{selected_text}{suffix}"
                self.text_buffer.delete(start, end)
                self.text_buffer.insert(start, replacement)
                
                if suffix:
                    new_iter = self.text_buffer.get_iter_at_mark(self.text_buffer.get_insert())
                    new_iter.backward_chars(len(suffix))
                    self.text_buffer.place_cursor(new_iter)
            else:
                mark = self.text_buffer.get_insert()
                iter_at_mark = self.text_buffer.get_iter_at_mark(mark)
                
                if prefix.startswith('#') and not iter_at_mark.starts_line():
                    iter_at_mark.set_line_offset(0)
                    self.text_buffer.place_cursor(iter_at_mark)
                
                self.text_buffer.insert_at_cursor(f"{prefix}{suffix}")
                
                if suffix:
                    new_iter = self.text_buffer.get_iter_at_mark(mark)
                    new_iter.backward_chars(len(suffix))
                    self.text_buffer.place_cursor(new_iter)
                    
        except Exception as e:
            print(f"Error inserting format: {e}")

    def insert_link_markup(self, _button=None):
        if not hasattr(self, "text_buffer"):
            return

        selected_text = ""
        bounds = self.text_buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            selected_text = self.text_buffer.get_text(start, end, False)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        text_entry = Gtk.Entry()
        text_entry.set_placeholder_text(_("Link text"))
        text_entry.set_text(selected_text or "")
        content.append(text_entry)

        url_entry = Gtk.Entry()
        url_entry.set_placeholder_text(_("URL"))
        url_entry.set_text("https://")
        content.append(url_entry)

        _form_dialog(
            _("Insert link"),
            content,
            lambda: self.apply_inserted_link(text_entry.get_text(), url_entry.get_text()),
            self,
            _("Insert"),
        )

    def insert_image_markup(self, _button=None):
        if not hasattr(self, "text_buffer"):
            return

        try:
            bounds = self.text_buffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                selected_text = self.text_buffer.get_text(start, end, False).strip()
                if self._looks_like_image_path(selected_text):
                    alt_text = os.path.basename(selected_text)
                    replacement = f"![{alt_text}]({selected_text})"
                else:
                    replacement = f"![{selected_text}](image.png)"
                self.text_buffer.delete(start, end)
                self.text_buffer.insert(start, replacement)
                return

            image_filter = Gtk.FileFilter()
            image_filter.set_name(_("Images"))
            for suffix in ("png", "jpg", "jpeg", "gif", "webp", "svg"):
                image_filter.add_suffix(suffix)

            any_filter = Gtk.FileFilter()
            any_filter.set_name(_("All files"))
            any_filter.add_pattern("*")

            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(image_filter)
            filters.append(any_filter)

            dialog = Gtk.FileDialog()
            dialog.set_title(_("Select image"))
            dialog.set_filters(filters)
            dialog.set_default_filter(image_filter)
            dialog.open(self, None, self.on_insert_image_dialog_response)
        except Exception as e:
            print(f"Error inserting image: {e}")

    def _looks_like_image_path(self, text):
        lowered = text.lower().strip().strip('"').strip("'")
        return lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"))

    def on_insert_image_dialog_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
        except GLib.Error as error:
            if not error.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED):
                print(f"Error selecting image: {error.message}")
            return

        if not file or not file.get_path():
            return

        image_path = file.get_path()
        display_path = image_path
        if getattr(self, "current_file", None):
            try:
                display_path = os.path.relpath(image_path, os.path.dirname(self.current_file))
            except ValueError:
                display_path = image_path
        alt_text = os.path.basename(image_path)
        self.text_buffer.insert_at_cursor(f"![{alt_text}]({display_path})")

    def apply_inserted_link(self, link_text, url):
        link_text = (link_text or "").strip() or _("Link")
        url = (url or "").strip() or "https://"
        self._replace_selection_or_insert(f"[{link_text}]({url})")
    
    def insert_list_item(self, list_type):
        if not hasattr(self, 'text_buffer'):
            return
            
        try:
            mark = self.text_buffer.get_insert()
            iter_at_mark = self.text_buffer.get_iter_at_mark(mark)
            
            iter_at_mark.set_line_offset(0)
            self.text_buffer.place_cursor(iter_at_mark)
            
            if list_type == "unordered":
                text = f"- {_('List item')}\n"
            elif list_type == "ordered":
                text = f"1. {_('List item')}\n"
            elif list_type == "task":
                text = f"- [ ] {_('Task item')}\n"
            else:
                return
            
            self.text_buffer.insert_at_cursor(text)
            self.in_list_context = True
            
        except Exception as e:
            print(f"Error inserting list: {e}")
    
    def insert_table(self, button):
        if not hasattr(self, 'text_buffer'):
            return

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        rows_spin = Gtk.SpinButton.new_with_range(2, 20, 1)
        rows_spin.set_value(3)
        cols_spin = Gtk.SpinButton.new_with_range(2, 10, 1)
        cols_spin.set_value(3)

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)

        rows_label = Gtk.Label(label=_("Rows"))
        rows_label.set_halign(Gtk.Align.START)
        rows_label.set_valign(Gtk.Align.CENTER)
        rows_label.set_xalign(0)
        rows_spin.set_valign(Gtk.Align.CENTER)
        grid.attach(rows_label, 0, 0, 1, 1)
        grid.attach(rows_spin, 1, 0, 1, 1)

        cols_label = Gtk.Label(label=_("Columns"))
        cols_label.set_halign(Gtk.Align.START)
        cols_label.set_valign(Gtk.Align.CENTER)
        cols_label.set_xalign(0)
        cols_spin.set_valign(Gtk.Align.CENTER)
        grid.attach(cols_label, 0, 1, 1, 1)
        grid.attach(cols_spin, 1, 1, 1, 1)

        content.append(grid)

        _form_dialog(
            _("Insert table"),
            content,
            lambda: self.apply_inserted_table(int(rows_spin.get_value()), int(cols_spin.get_value())),
            self,
            _("Insert"),
        )

    def apply_inserted_table(self, rows, cols):
        self._replace_selection_or_insert(self.build_markdown_table(rows, cols))

    @staticmethod
    def build_markdown_table(rows, cols):
        header_cells = [f"Header {index}" for index in range(1, cols + 1)]
        separator_cells = ["---"] * cols
        lines = [
            "| " + " | ".join(header_cells) + " |",
            "| " + " | ".join(separator_cells) + " |",
        ]
        for row_index in range(1, rows):
            cells = [f"Cell {row_index}-{column_index}" for column_index in range(1, cols + 1)]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines) + "\n"

    def on_key_pressed(self, controller, keyval, keycode, state):
        try:
            if keyval == Gdk.KEY_Return or keyval == Gdk.KEY_KP_Enter:
                return self.handle_enter_key()
            return False
        except Exception as e:
            print(f"Error handling key: {e}")
            return False
    
    def handle_enter_key(self):
        if not hasattr(self, 'text_buffer'):
            return False
            
        try:
            mark = self.text_buffer.get_insert()
            iter_at_cursor = self.text_buffer.get_iter_at_mark(mark)
            
            line_start = iter_at_cursor.copy()
            line_start.set_line_offset(0)
            line_end = iter_at_cursor.copy()
            if not line_end.ends_line():
                line_end.forward_to_line_end()
            
            current_line = self.text_buffer.get_text(line_start, line_end, False)
            
            continuation = self.get_list_continuation_prefix(current_line)
            if continuation is not None:
                if continuation == "":
                    self.text_buffer.delete(line_start, iter_at_cursor)
                    self.in_list_context = False
                    return False

                self.text_buffer.insert_at_cursor(f"\n{continuation}")
                return True
            
            self.in_list_context = False
            return False

            
        except Exception as e:
            print(f"Error handling Enter: {e}")
            return False

    @classmethod
    def get_list_continuation_prefix(cls, current_line):
        for pattern, pattern_type in cls.LIST_CONTINUATION_PATTERNS:
            match = pattern.match(current_line)
            if not match:
                continue

            if pattern_type == "task":
                indent, content = match.groups()
                return "" if not content.strip() else f"{indent}- [ ] "

            if pattern_type == "ordered":
                indent, number, content = match.groups()
                if not content.strip():
                    return ""
                return f"{indent}{int(number) + 1}. "

            indent, content = match.groups()
            if not content.strip():
                return ""

            bullet_map = {
                "unordered_dash": "- ",
                "unordered_star": "* ",
                "unordered_plus": "+ ",
            }
            return f"{indent}{bullet_map[pattern_type]}"

        return None

    def _replace_selection_or_insert(self, text):
        bounds = self.text_buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            self.text_buffer.delete(start, end)
            self.text_buffer.insert(start, text)
        else:
            self.text_buffer.insert_at_cursor(text)
    
    def update_cursor_position(self):
        if not hasattr(self, 'text_buffer') or not hasattr(self, 'cursor_label'):
            return
            
        try:
            mark = self.text_buffer.get_insert()
            iter_at_mark = self.text_buffer.get_iter_at_mark(mark)
            line = iter_at_mark.get_line() + 1
            col = iter_at_mark.get_line_offset() + 1
            self.cursor_label.set_text(f"{_('Line')} {line}, {_('Col')} {col}")
        except Exception as e:
            print(f"Error updating cursor position: {e}")
    
    def update_detailed_stats(self, text):
        if not text:
            text = ""
            
        try:
            stats = DocumentService.compute_stats(text)
            
            if hasattr(self, 'lines_label'):
                self.lines_label.set_text(f"{stats.lines} {_('lines')}")
            if hasattr(self, 'words_label'):
                self.words_label.set_text(f"{stats.words} {_('words')}")
            if hasattr(self, 'chars_label'):
                self.chars_label.set_text(f"{stats.characters} {_('chars')}")
            if hasattr(self, 'headers_label'):
                self.headers_label.set_text(f"{stats.headers} {_('headers')}")
            if hasattr(self, 'reading_time_label'):
                self.reading_time_label.set_text(f"{stats.reading_time_minutes} {_('min read')}")
            
            if stats.size_bytes < 1024:
                size_text = f"{stats.size_bytes} B"
            elif stats.size_bytes < 1024 * 1024:
                size_text = f"{stats.size_bytes / 1024:.1f} KB"
            else:
                size_text = f"{stats.size_bytes / (1024 * 1024):.1f} MB"
            
            if hasattr(self, 'size_label'):
                self.size_label.set_text(size_text)
                
            self.update_cursor_position()
            if hasattr(self, 'update_outline'):
                self.update_outline(text)
            
        except Exception as e:
            print(f"Error updating statistics: {e}")

    def update_cursor_position(self):
        if not hasattr(self, 'text_buffer') or not hasattr(self, 'cursor_label'):
            return
            
        try:
            mark = self.text_buffer.get_insert()
            iter_at_mark = self.text_buffer.get_iter_at_mark(mark)
            line = iter_at_mark.get_line() + 1
            col = iter_at_mark.get_line_offset() + 1
            self.cursor_label.set_text(f"{_('Line')} {line}, {_('Col')} {col}")
        except Exception as e:
            print(f"Error updating cursor position: {e}")

    def on_text_changed(self, buffer):
        try:
            self.document_modified = True
            
            if hasattr(self, 'save_btn'):
                self.save_btn.set_sensitive(True)
            
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            
            if hasattr(self, 'render_preview'):
                self.render_preview(text)
            
            self.update_detailed_stats(text)
            
            if hasattr(self, 'doc_status_label'):
                self.doc_status_label.set_text(_("Modified"))
            
            if hasattr(self, 'update_search_if_active'):
                self.update_search_if_active()
            
        except Exception as e:
            print(f"Error in on_text_changed: {e}")
    
    def set_view_mode(self, mode):
        if not hasattr(self, 'paned'):
            return
            
        try:
            # Update buttons style
            for btn_name in ['split_view_btn', 'editor_view_btn', 'preview_view_btn']:
                if hasattr(self, btn_name):
                    getattr(self, btn_name).remove_css_class("view-btn-active")
            
            editor_widget = self.paned.get_start_child()
            preview_widget = self.paned.get_end_child()
            
            if mode == "split":
                if editor_widget: 
                    editor_widget.set_visible(True)
                if preview_widget: 
                    preview_widget.set_visible(True)
                
                # Try to restore a reasonable position
                width = self.get_width() if hasattr(self, 'get_width') else 1000
                current_pos = self.paned.get_position()
                if current_pos <= 50 or current_pos >= width - 50:
                    self.paned.set_position(int(width / 2))
                
                if hasattr(self, 'split_view_btn'):
                    self.split_view_btn.add_css_class("view-btn-active")
                    
            elif mode == "editor":
                if editor_widget: 
                    editor_widget.set_visible(True)
                if preview_widget: 
                    preview_widget.set_visible(False)
                if hasattr(self, 'editor_view_btn'):
                    self.editor_view_btn.add_css_class("view-btn-active")
                    
            elif mode == "preview":
                if editor_widget: 
                    editor_widget.set_visible(False)
                if preview_widget: 
                    preview_widget.set_visible(True)
                if hasattr(self, 'preview_view_btn'):
                    self.preview_view_btn.add_css_class("view-btn-active")
            
            self.current_view_mode = mode
                
        except Exception as e:
            print(f"Error changing view mode: {e}")
