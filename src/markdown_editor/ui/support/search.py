from gi.repository import Gtk, Pango

from ...core.i18n import translate as _


class SearchMixin:
    def create_search_bar(self):
        if not Gtk:
            return None
            
        search_bar = Gtk.SearchBar()
        search_bar.set_search_mode(False)

        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        search_box.set_spacing(6)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(6)
        search_box.set_margin_bottom(6)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text(_("Search in document..."))
        self.search_entry.add_css_class("compact-entry")
        self.search_entry.set_size_request(-1, 30)
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.append(self.search_entry)

        self.replace_entry = Gtk.Entry()
        self.replace_entry.set_placeholder_text(_("Replace with..."))
        self.replace_entry.add_css_class("compact-entry")
        self.replace_entry.set_size_request(180, 30)
        search_box.append(self.replace_entry)

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        nav_box.add_css_class("linked")

        self.prev_button = Gtk.Button()
        self.prev_button.set_icon_name("go-up-symbolic")
        self.prev_button.set_tooltip_text(_("Previous"))
        self.prev_button.connect("clicked", self.on_search_previous)
        nav_box.append(self.prev_button)

        self.next_button = Gtk.Button()
        self.next_button.set_icon_name("go-down-symbolic")
        self.next_button.set_tooltip_text(_("Next"))
        self.next_button.connect("clicked", self.on_search_next)
        nav_box.append(self.next_button)

        search_box.append(nav_box)

        replace_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        replace_box.add_css_class("linked")

        self.replace_button = Gtk.Button(label=_("Replace"))
        self.replace_button.connect("clicked", self.on_replace_current)
        replace_box.append(self.replace_button)

        self.replace_all_button = Gtk.Button(label=_("Replace all"))
        self.replace_all_button.connect("clicked", self.on_replace_all)
        replace_box.append(self.replace_all_button)

        search_box.append(replace_box)

        self.search_results_label = Gtk.Label()
        self.search_results_label.add_css_class("dim-label")
        self.search_results_label.set_margin_start(12)
        search_box.append(self.search_results_label)

        search_bar.set_child(search_box)
        search_bar.connect_entry(self.search_entry)

        return search_bar
    
    def setup_search_tags(self):
        if not hasattr(self, 'text_buffer') or not Pango:
            return
            
        self.search_matches = []
        self.current_search_index = -1
        
        self.search_tag = self.text_buffer.create_tag("search_highlight")
        self.search_tag.set_property("background", "#ffff00")
        self.search_tag.set_property("weight", Pango.Weight.BOLD)

        self.current_search_tag = self.text_buffer.create_tag("current_search_highlight")
        self.current_search_tag.set_property("background", "#ff6600")
        self.current_search_tag.set_property("weight", Pango.Weight.BOLD)

    def toggle_search(self):
        if not hasattr(self, 'search_bar'):
            return
            
        is_active = not self.search_bar.get_search_mode()
        self.search_bar.set_search_mode(is_active)
        if is_active:
            selected_text = self.get_selected_search_text()
            if selected_text and hasattr(self, 'search_entry'):
                self.search_entry.set_text(selected_text)
            self.search_entry.grab_focus()
            self.search_entry.select_region(0, -1)

    def get_selected_search_text(self):
        if not hasattr(self, 'text_buffer'):
            return ""

        bounds = self.text_buffer.get_selection_bounds()
        if not bounds:
            return ""

        start, end = bounds
        selected_text = self.text_buffer.get_text(start, end, False)
        return self.normalize_search_selection(selected_text)

    @staticmethod
    def normalize_search_selection(selected_text):
        return " ".join((selected_text or "").split())
    
    def hide_search(self):
        if hasattr(self, 'search_bar'):
            self.search_bar.set_search_mode(False)
        self.clear_search_highlights()
        if hasattr(self, 'text_view'):
            self.text_view.grab_focus()
        if hasattr(self, 'replace_entry'):
            self.replace_entry.set_text("")
    
    def on_search_changed(self, entry):
        search_text = entry.get_text()
        if search_text:
            self.search_in_text(search_text)
        else:
            self.clear_search_highlights()
    
    def search_in_text(self, search_text):
        self.clear_search_highlights()
        
        if not search_text or not hasattr(self, 'text_buffer'):
            return
            
        buffer_text = self.text_buffer.get_text(
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter(),
            False
        )
        
        self.search_matches = []
        start = 0
        while True:
            pos = buffer_text.lower().find(search_text.lower(), start)
            if pos == -1:
                break
            self.search_matches.append((pos, pos + len(search_text)))
            start = pos + 1
        
        for start_pos, end_pos in self.search_matches:
            start_iter = self.text_buffer.get_start_iter()
            start_iter.forward_chars(start_pos)
            end_iter = self.text_buffer.get_start_iter()
            end_iter.forward_chars(end_pos)
            self.text_buffer.apply_tag(self.search_tag, start_iter, end_iter)
        
        if self.search_matches:
            self.current_search_index = 0
            self.highlight_current_match()
            if hasattr(self, 'search_results_label'):
                self.search_results_label.set_text(f"{len(self.search_matches)} {_('matches')}")
        else:
            self.current_search_index = -1
            if hasattr(self, 'search_results_label'):
                self.search_results_label.set_text(_("No matches"))
    
    def highlight_current_match(self):
        if (self.current_search_index >= 0 and 
            self.current_search_index < len(self.search_matches) and
            hasattr(self, 'text_buffer')):
            
            start_iter = self.text_buffer.get_start_iter()
            end_iter = self.text_buffer.get_end_iter()
            self.text_buffer.remove_tag(self.current_search_tag, start_iter, end_iter)
            
            start_pos, end_pos = self.search_matches[self.current_search_index]
            start_iter = self.text_buffer.get_start_iter()
            start_iter.forward_chars(start_pos)
            end_iter = self.text_buffer.get_start_iter()
            end_iter.forward_chars(end_pos)
            
            self.text_buffer.apply_tag(self.current_search_tag, start_iter, end_iter)
            
            if hasattr(self, 'text_view'):
                self.text_view.scroll_to_iter(start_iter, 0.1, False, 0.0, 0.0)
            
            if hasattr(self, 'search_results_label'):
                self.search_results_label.set_text(f"{self.current_search_index + 1} {_('of')} {len(self.search_matches)}")
    
    def on_search_next(self, button):
        if self.search_matches:
            self.current_search_index = (self.current_search_index + 1) % len(self.search_matches)
            self.highlight_current_match()
    
    def on_search_previous(self, button):
        if self.search_matches:
            self.current_search_index = (self.current_search_index - 1) % len(self.search_matches)
            self.highlight_current_match()

    def on_replace_current(self, button):
        if not self.search_matches or self.current_search_index < 0 or not hasattr(self, 'text_buffer'):
            return

        replacement = self.replace_entry.get_text() if hasattr(self, 'replace_entry') else ""
        start_pos, end_pos = self.search_matches[self.current_search_index]

        start_iter = self.text_buffer.get_start_iter()
        start_iter.forward_chars(start_pos)
        end_iter = self.text_buffer.get_start_iter()
        end_iter.forward_chars(end_pos)

        self.text_buffer.begin_user_action()
        self.text_buffer.delete(start_iter, end_iter)
        self.text_buffer.insert(start_iter, replacement)
        self.text_buffer.end_user_action()

        self.search_in_text(self.search_entry.get_text())

    def on_replace_all(self, button):
        search_text = self.search_entry.get_text() if hasattr(self, 'search_entry') else ""
        if not search_text or not hasattr(self, 'text_buffer'):
            return

        replacement = self.replace_entry.get_text() if hasattr(self, 'replace_entry') else ""
        text = self.text_buffer.get_text(
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter(),
            False
        )
        replaced_text = text.replace(search_text, replacement)

        self.text_buffer.begin_user_action()
        self.text_buffer.set_text(replaced_text)
        self.text_buffer.end_user_action()
        self.search_in_text(search_text)
    
    def clear_search_highlights(self):
        if not hasattr(self, 'text_buffer'):
            return
            
        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()
        
        if hasattr(self, 'search_tag'):
            self.text_buffer.remove_tag(self.search_tag, start_iter, end_iter)
        if hasattr(self, 'current_search_tag'):
            self.text_buffer.remove_tag(self.current_search_tag, start_iter, end_iter)
            
        self.search_matches = []
        self.current_search_index = -1
        
        if hasattr(self, 'search_results_label'):
            self.search_results_label.set_text("")
    
    def update_search_if_active(self):
        if (hasattr(self, 'search_bar') and hasattr(self, 'search_entry') and
            self.search_bar.get_search_mode() and self.search_entry.get_text()):
            self.search_in_text(self.search_entry.get_text())
