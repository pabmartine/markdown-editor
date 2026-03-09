from gi.repository import GLib

try:
    import gi
    gi.require_version("JavaScriptCore", "6.0")
    from gi.repository import JavaScriptCore
except Exception:
    JavaScriptCore = None


class ScrollSyncMixin:
    def setup_scroll_sync(self):
        if not hasattr(self, 'editor_scroll') or not hasattr(self, 'preview_scroll'):
            return
            
        self.sync_scroll_enabled = True
        self.click_in_progress = False
        
        self.editor_vadj = self.editor_scroll.get_vadjustment()
        self.preview_vadj = self.preview_scroll.get_vadjustment()
        
        self.editor_vadj.connect("value-changed", self.on_editor_scroll)
        if hasattr(self, "preview_webview"):
            self.preview_scroll_poll_pending = False
            self.preview_scroll_poll_id = GLib.timeout_add(120, self.poll_preview_scroll)
        else:
            self.preview_vadj.connect("value-changed", self.on_preview_scroll)
    
    def on_preview_clicked(self, gesture, n_press, x, y):
        self.click_in_progress = True
        
        def reactivate_sync():
            self.click_in_progress = False
            return False
            
        if GLib:
            GLib.timeout_add(200, reactivate_sync)
        
        return False

    def on_editor_scroll(self, adjustment):
        if not self.sync_scroll_enabled or self.click_in_progress:
            return
            
        if adjustment.get_upper() - adjustment.get_page_size() > 0:
            ratio = adjustment.get_value() / (adjustment.get_upper() - adjustment.get_page_size())
            if hasattr(self, "preview_webview"):
                self.set_preview_scroll_ratio(ratio)
            else:
                self.sync_scroll_enabled = False
                try:
                    preview_max = self.preview_vadj.get_upper() - self.preview_vadj.get_page_size()
                    if preview_max > 0:
                        new_value = ratio * preview_max
                        self.preview_vadj.set_value(new_value)
                finally:
                    self.sync_scroll_enabled = True

    def on_preview_scroll(self, adjustment):
        if not self.sync_scroll_enabled or self.click_in_progress:
            return
            
        if adjustment.get_upper() - adjustment.get_page_size() > 0:
            ratio = adjustment.get_value() / (adjustment.get_upper() - adjustment.get_page_size())
            
            self.sync_scroll_enabled = False
            try:
                editor_max = self.editor_vadj.get_upper() - self.editor_vadj.get_page_size()
                if editor_max > 0:
                    new_value = ratio * editor_max
                    self.editor_vadj.set_value(new_value)
            finally:
                self.sync_scroll_enabled = True

    def set_preview_scroll_ratio(self, ratio):
        if not hasattr(self, "preview_webview"):
            return
        script = f"window.__mdEditorSetScrollRatio({max(0.0, min(1.0, ratio))});"
        self.preview_webview.evaluate_javascript(script, -1, None, None, None, None, None)

    def poll_preview_scroll(self):
        if not hasattr(self, "preview_webview") or JavaScriptCore is None:
            return False
        if self.preview_scroll_poll_pending:
            return True

        self.preview_scroll_poll_pending = True
        self.preview_webview.evaluate_javascript(
            "window.__mdEditorGetScrollRatio();",
            -1,
            None,
            None,
            None,
            self.on_preview_scroll_ratio_evaluated,
            None,
        )
        return True

    def on_preview_scroll_ratio_evaluated(self, webview, result, _user_data):
        self.preview_scroll_poll_pending = False
        if not self.sync_scroll_enabled or self.click_in_progress:
            return

        try:
            value = webview.evaluate_javascript_finish(result)
            if not value or not value.is_number():
                return
            ratio = value.to_double()
        except Exception:
            return

        editor_max = self.editor_vadj.get_upper() - self.editor_vadj.get_page_size()
        if editor_max <= 0:
            return

        self.sync_scroll_enabled = False
        try:
            self.editor_vadj.set_value(max(0.0, min(1.0, ratio)) * editor_max)
        finally:
            self.sync_scroll_enabled = True
    
    def disable_scroll_sync(self):
        self.sync_scroll_enabled = False
    
    def enable_scroll_sync(self):
        self.sync_scroll_enabled = True
