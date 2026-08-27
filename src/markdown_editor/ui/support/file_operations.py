import os

from gi.repository import Adw, Gio, GLib, Gtk

from ...core.constants import MAX_RECENT_FILES
from ...core.i18n import translate as _


def _markdown_filters():
    filter_md = Gtk.FileFilter()
    filter_md.set_name(_("Markdown files"))
    filter_md.add_mime_type("text/markdown")
    for suffix in ("md", "markdown", "mdown", "mkd"):
        filter_md.add_suffix(suffix)

    filter_any = Gtk.FileFilter()
    filter_any.set_name(_("All files"))
    filter_any.add_pattern("*")

    filters = Gio.ListStore.new(Gtk.FileFilter)
    filters.append(filter_md)
    filters.append(filter_any)
    return filters, filter_md


def _dismissed(error):
    """True when the user simply closed the file chooser."""
    return error.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED)


class FileOperationsMixin:
    def get_recent_files(self):
        return [path for path in self.config.get("recent_files", []) if os.path.exists(path)]

    def add_recent_file(self, file_path):
        recent_files = [path for path in self.get_recent_files() if path != file_path]
        recent_files.insert(0, file_path)
        self.config.set("recent_files", recent_files[:MAX_RECENT_FILES])
        if hasattr(self, "refresh_recent_files_ui"):
            self.refresh_recent_files_ui()

    def open_recent_file(self, file_path):
        self.confirm_discard_changes(lambda: self.load_file(file_path))

    def has_unsaved_changes(self):
        return bool(getattr(self, "document_modified", False))

    def confirm_discard_changes(self, action):
        if not self.has_unsaved_changes():
            action()
            return

        dialog = Adw.AlertDialog.new(
            _("Unsaved changes"),
            _("The current document has unsaved changes.")
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("discard", _("Discard"))
        dialog.add_response("save", _("Save"))
        dialog.set_close_response("cancel")
        dialog.set_default_response("save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_unsaved_changes_response, action)
        dialog.present(self)

    def _on_unsaved_changes_response(self, dialog, response, action):
        if response == "discard":
            action()
        elif response == "save":
            self.save_document(action)

    def on_open(self, widget):
        if not Gtk:
            return

        self.confirm_discard_changes(self._show_open_dialog)

    def _show_open_dialog(self):
        dialog = Gtk.FileDialog()
        dialog.set_title(_("Open file"))
        filters, default_filter = _markdown_filters()
        dialog.set_filters(filters)
        dialog.set_default_filter(default_filter)
        dialog.open(self, None, self.on_open_dialog_response)

    def on_open_dialog_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
        except GLib.Error as error:
            if not _dismissed(error):
                self.show_error_dialog(f"{_('Error')}: {error.message}")
            return

        if file:
            self.load_file(file.get_path())
    
    def on_save(self, widget):
        self.save_document()

    def save_document(self, after_save=None):
        if self.current_file:
            if self.save_file():
                if after_save:
                    after_save()
                return True
            return False

        self.save_as(after_save=after_save)
        return None
    
    def save_as(self, after_save=None):
        if not Gtk:
            return

        self.pending_after_save = after_save
            
        dialog = Gtk.FileDialog()
        dialog.set_title(_("Save file"))
        dialog.set_initial_name(_("untitled.md"))
        filters, default_filter = _markdown_filters()
        dialog.set_filters(filters)
        dialog.set_default_filter(default_filter)
        dialog.save(self, None, self.on_save_dialog_response)

    def on_save_dialog_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
        except GLib.Error as error:
            self.pending_after_save = None
            if not _dismissed(error):
                self.show_error_dialog(f"{_('Error')}: {error.message}")
            return

        if not file:
            self.pending_after_save = None
            return

        self.current_file = file.get_path()
        if not self.save_file():
            self.pending_after_save = None
            return

        self.update_title()
        self.update_header()
        if self.pending_after_save:
            callback = self.pending_after_save
            self.pending_after_save = None
            callback()
    
    def load_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if hasattr(self, 'text_buffer'):
                self.text_buffer.set_text(content)
                
            self.current_file = file_path
            self.document_modified = False
            self.add_recent_file(file_path)
            
            if hasattr(self, 'save_btn'):
                self.save_btn.set_sensitive(False)
            
            filename = os.path.basename(file_path)
            self.set_title(f"{filename} - {_('Markdown Editor')}")
            
            if hasattr(self, 'doc_status_label'):
                self.doc_status_label.set_text(_("Ready"))
            
            if (hasattr(self, 'content_stack') and 
                self.content_stack.get_visible_child_name() == "welcome"):
                self.show_editor_state()
            
            if hasattr(self, 'text_view'):
                self.text_view.grab_focus()
                
            if hasattr(self, 'clear_search_highlights'):
                self.clear_search_highlights()
            
        except Exception as e:
            print(f"Error loading file: {e}")
            self.show_error_dialog(f"{_('Error')}: {str(e)}")
    
    def save_file(self):
        if not self.current_file:
            self.save_as()
            return None
            
        try:
            if hasattr(self, 'text_buffer'):
                text = self.text_buffer.get_text(
                    self.text_buffer.get_start_iter(),
                    self.text_buffer.get_end_iter(),
                    False
                )
            else:
                text = ""
                
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(text)
            
            self.document_modified = False
            
            if hasattr(self, 'save_btn'):
                self.save_btn.set_sensitive(False)
                
            filename = os.path.basename(self.current_file)
            self.set_title(f"{filename} - {_('Markdown Editor')}")
            self.add_recent_file(self.current_file)
            
            if hasattr(self, 'doc_status_label'):
                self.doc_status_label.set_text(_("Saved"))
            return True
            
        except Exception as e:
            print(f"Error saving file: {e}")
            self.show_error_dialog(f"{_('Error')}: {str(e)}")
            return False
    
    def show_error_dialog(self, message):
        if not Adw:
            print(f"Error: {message}")
            return
            
        dialog = Adw.AlertDialog.new(_("Error"), message)
        dialog.add_response("ok", _("Close"))
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.present(self)
    
    def update_title(self):
        if self.current_file:
            filename = os.path.basename(self.current_file)
            self.set_title(f"{filename} - {_('Markdown Editor')}")
        else:
            self.set_title(f"{_('New document')} - {_('Markdown Editor')}")

    def update_header(self):
        pass

    def request_close(self):
        self.pending_close = True
        self.close()
    
    def on_new_from_welcome(self, widget):
        self.current_file = None
        self.document_modified = False
        
        if hasattr(self, 'save_btn'):
            self.save_btn.set_sensitive(False)
        
        if hasattr(self, 'text_buffer'):
            self.text_buffer.set_text("")
        
        self.set_title(f"{_('New document')} - {_('Markdown Editor')}")
        
        if hasattr(self, 'show_editor_state'):
            self.show_editor_state()
        
        if hasattr(self, 'text_view'):
            self.text_view.grab_focus()
            
        if hasattr(self, 'clear_search_highlights'):
            self.clear_search_highlights()

    def on_open_from_welcome(self, widget):
        self.on_open(widget)

    def close_current_document(self):
        self.current_file = None
        self.document_modified = False

        if hasattr(self, "text_buffer"):
            self.text_buffer.set_text("")

        if hasattr(self, "save_btn"):
            self.save_btn.set_sensitive(False)

        if hasattr(self, "doc_status_label"):
            self.doc_status_label.set_text(_("Ready"))

        if hasattr(self, "clear_search_highlights"):
            self.clear_search_highlights()

        if hasattr(self, "search_bar"):
            self.search_bar.set_visible(False)

        if hasattr(self, "outline_visible"):
            self.outline_visible = False
        if hasattr(self, "outline_panel"):
            self.outline_panel.set_visible(False)
        if hasattr(self, "outline_toggle_btn"):
            self.outline_toggle_btn.remove_css_class("view-btn-active")

        if hasattr(self, "session_service"):
            self.session_service.clear_recovery()
        self.config.set("last_session_dirty", False)

        self.set_title(_("Markdown Editor"))
        if hasattr(self, "show_welcome_state"):
            self.show_welcome_state()

    def on_close_file(self, _button):
        self.confirm_discard_changes(self.close_current_document)
    
    def on_new(self, button):
        try:
            if (hasattr(self, 'content_stack') and
                self.content_stack.get_visible_child_name() == "welcome"):
                self.on_new_from_welcome(None)
                return

            def create_new_document():
                if hasattr(self, 'text_buffer'):
                    self.text_buffer.set_text("")

                self.current_file = None
                self.document_modified = False

                if hasattr(self, 'save_btn'):
                    self.save_btn.set_sensitive(False)

                self.set_title(f"{_('New document')} - {_('Markdown Editor')}")

                if hasattr(self, 'clear_search_highlights'):
                    self.clear_search_highlights()

                if hasattr(self, 'text_view'):
                    self.text_view.grab_focus()

            self.confirm_discard_changes(create_new_document)
        except Exception as e:
            print(f"Error creating new document: {e}")
