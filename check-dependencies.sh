#!/usr/bin/env python3

"""
Editor de Markdown con vista previa mejorada
"""

import sys
import os
import json
import re
import traceback
import base64
from html.parser import HTMLParser

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Gio, GLib, Pango, Gdk, GdkPixbuf, Adw
    GTK_VERSION = 4
except Exception as e:
    traceback.print_exc()
    sys.exit(1)

MARKDOWN_AVAILABLE = False
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    pass

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "markdown-editor")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class Config:
    def __init__(self):
        self.config = {
            "window_width": 1000,
            "window_height": 700,
            "paned_position": 500,
            "dark_theme": False,
            "language": "auto",
            "render_style": "default",
        }
        try:
            self.load_config()
        except Exception:
            pass
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.config.update(json.load(f))
    
    def save_config(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()

class ImprovedRenderer:
    def __init__(self, style="default"):
        self.style = style
    
    def set_style(self, style):
        self.style = style
    
    def render_text(self, markdown_text):
        try:
            if MARKDOWN_AVAILABLE:
                extensions = [
                    'tables',            # Soporte de tablas
                    'fenced_code',       # Bloques de código con ```
                    'sane_lists',        # Listas más predecibles
                    'nl2br',             # Saltos de línea simples
                    'smarty',            # Comillas tipográficas
                ]
                html = markdown.markdown(markdown_text, extensions=extensions)
                return self._html_to_pango(html)
        except Exception:
            pass
        return self._basic_render(markdown_text)
    
    def _html_to_pango(self, html):
        class HTMLToPangoParser(HTMLParser):
            def __init__(self, style):
                super().__init__()
                self.output = []
                self.tag_stack = []
                self.list_level = 0
                self.in_code_block = False
                self.table_column = 0
                self.in_heading_level = None
                self.style = style
                
            def handle_starttag(self, tag, attrs):
                self.tag_stack.append(tag)
                
                if tag == 'h1':
                    self.in_heading_level = 1
                    if self.style == "github":
                        self.output.append('\n<span size="26000" weight="bold">')
                    elif self.style == "gitlab":
                        self.output.append('\n<span size="25000" weight="bold" foreground="#1f883d">')
                    else:
                        self.output.append('\n<span size="24000" weight="bold">')
                elif tag == 'h2':
                    self.in_heading_level = 2
                    if self.style == "github":
                        self.output.append('\n<span size="22000" weight="bold">')
                    elif self.style == "gitlab":
                        self.output.append('\n<span size="21000" weight="bold" foreground="#0969da">')
                    else:
                        self.output.append('\n<span size="20000" weight="bold">')
                elif tag == 'h3':
                    self.in_heading_level = 3
                    size = "20000" if self.style == "github" else "19000" if self.style == "gitlab" else "18000"
                    self.output.append(f'\n<span size="{size}" weight="bold">')
                elif tag == 'h4':
                    self.in_heading_level = 4
                    size = "18000" if self.style == "github" else "17000" if self.style == "gitlab" else "16000"
                    self.output.append(f'\n<span size="{size}" weight="bold">')
                elif tag == 'h5':
                    self.in_heading_level = 5
                    size = "16000" if self.style == "github" else "15000" if self.style == "gitlab" else "14000"
                    self.output.append(f'\n<span size="{size}" weight="bold">')
                elif tag == 'h6':
                    self.in_heading_level = 6
                    size = "14000" if self.style == "github" else "13000" if self.style == "gitlab" else "12000"
                    self.output.append(f'\n<span size="{size}" weight="bold">')
                elif tag == 'strong' or tag == 'b':
                    self.output.append('<b>')
                elif tag == 'em' or tag == 'i':
                    self.output.append('<i>')
                elif tag == 'u':
                    self.output.append('<u>')
                elif tag == 'code':
                    if not self.in_code_block:
                        if self.style == "github":
                            self.output.append('<span font_family="monospace" background="#f6f8fa" foreground="#d1242f">')
                        elif self.style == "gitlab":
                            self.output.append('<span font_family="monospace" background="#fdf6e3" foreground="#bf616a">')
                        else:
                            self.output.append('<span font_family="monospace" background="#e0e0e0">')
                elif tag == 'pre':
                    self.in_code_block = True
                    if self.style == "github":
                        self.output.append('\n<span font_family="monospace" background="#f6f8fa">')
                    elif self.style == "gitlab":
                        self.output.append('\n<span font_family="monospace" background="#fdf6e3">')
                    else:
                        self.output.append('\n<span font_family="monospace" background="#e3e3e3">')
                elif tag == 'p':
                    if self.output and not self.output[-1].endswith('\n'):
                        self.output.append('\n')
                elif tag == 'br':
                    self.output.append('\n')
                elif tag == 'hr':
                    if self.style == "github":
                        self.output.append('\n' + '─' * 50 + '\n')
                    elif self.style == "gitlab":
                        self.output.append('\n<span foreground="#e1e4e8">' + '─' * 50 + '</span>\n')
                    else:
                        self.output.append('\n' + '─' * 50 + '\n')
                elif tag == 'blockquote':
                    if self.style == "github":
                        self.output.append('\n<span style="italic" foreground="#656d76">▌ ')
                    elif self.style == "gitlab":
                        self.output.append('\n<span style="italic" foreground="#6a737d">│ ')
                    else:
                        self.output.append('\n<span style="italic" foreground="#666666">" ')
                elif tag == 'ul':
                    self.list_level += 1
                    self.output.append('\n')
                elif tag == 'ol':
                    self.list_level += 1
                    self.output.append('\n')
                elif tag == 'li':
                    indent = '  ' * (self.list_level - 1)
                    parent_tag = self.tag_stack[-2] if len(self.tag_stack) > 1 else None
                    if parent_tag == 'ul':
                        if self.style == "github":
                            self.output.append(f'{indent}• ')
                        elif self.style == "gitlab":
                            self.output.append(f'{indent}• ')
                        else:
                            self.output.append(f'{indent}• ')
                    elif parent_tag == 'ol':
                        self.output.append(f'{indent}1. ')
                    else:
                        self.output.append(f'{indent}• ')
                elif tag == 'del' or tag == 's':
                    self.output.append('<s>')
                elif tag == 'a':
                    href = next((value for name, value in attrs if name == 'href'), '#')
                    if self.style == "github":
                        self.output.append('<span foreground="#0969da" underline="single">')
                    elif self.style == "gitlab":
                        self.output.append('<span foreground="#1068bf" underline="single">')
                    else:
                        self.output.append('<span foreground="blue" underline="single">')
                elif tag == 'img':
                    alt = next((value for name, value in attrs if name == 'alt'), 'Image')
                    src = next((value for name, value in attrs if name == 'src'), '')
                    self.output.append(f'\n🖼️ [Imagen: {alt}]\n')
                elif tag == 'table':
                    self.output.append('\n<span font_family="monospace">')
                elif tag == 'tr':
                    self.table_column = 0
                    self.output.append('\n')
                elif tag == 'td' or tag == 'th':
                    if self.table_column > 0:
                        self.output.append(' | ')
                    self.table_column += 1
                    if tag == 'th':
                        self.output.append('<b>')
                
            def handle_endtag(self, tag):
                if self.tag_stack and self.tag_stack[-1] == tag:
                    self.tag_stack.pop()
                
                if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    self.output.append('</span>\n')
                    if self.in_heading_level == 1:
                        if self.style == "github":
                            self.output.append('<span foreground="#d0d7de">' + '─' * 60 + '</span>\n')
                        elif self.style == "gitlab":
                            self.output.append('<span foreground="#c9c9c9">' + '─' * 60 + '</span>\n')
                        else:
                            self.output.append('<span foreground="#c9c9c9">' + '─' * 60 + '</span>\n')
                    elif self.in_heading_level == 2:
                        if self.style == "github":
                            self.output.append('<span foreground="#d8d8d8">' + '─' * 50 + '</span>\n')
                        elif self.style == "gitlab":
                            self.output.append('<span foreground="#d8d8d8">' + '─' * 50 + '</span>\n')
                        else:
                            self.output.append('<span foreground="#d8d8d8">' + '─' * 50 + '</span>\n')
                    self.in_heading_level = None
                elif tag == 'strong' or tag == 'b':
                    self.output.append('</b>')
                elif tag == 'em' or tag == 'i':
                    self.output.append('</i>')
                elif tag == 'u':
                    self.output.append('</u>')
                elif tag == 'del' or tag == 's':
                    self.output.append('</s>')
                elif tag == 'code':
                    if not self.in_code_block:
                        self.output.append('</span>')
                elif tag == 'pre':
                    self.in_code_block = False
                    self.output.append('</span>\n')
                elif tag == 'p':
                    self.output.append('\n')
                elif tag == 'blockquote':
                    self.output.append(' "</span>\n' if self.style == "default" else '</span>\n')
                elif tag == 'ul' or tag == 'ol':
                    self.list_level -= 1
                    self.output.append('\n')
                elif tag == 'li':
                    self.output.append('\n')
                elif tag == 'a':
                    self.output.append('</span>')
                elif tag == 'table':
                    self.output.append('</span>\n')
                elif tag == 'th':
                    self.output.append('</b>')
                
            def handle_data(self, data):
                data = data.replace('&', '&amp;')
                data = data.replace('<', '&lt;')
                data = data.replace('>', '&gt;')
                self.output.append(data)
                
            def get_pango(self):
                result = ''.join(self.output)
                result = re.sub(r'\n{3,}', '\n\n', result)
                return result.strip()
        
        parser = HTMLToPangoParser(self.style)
        parser.feed(html)
        return parser.get_pango()
    
    def _basic_render(self, text):
        lines = text.split('\n')
        result = []
        in_code_block = False
        
        for line in lines:
            original_line = line
            stripped_line = line.strip()
            
            if stripped_line.startswith('```'):
                in_code_block = not in_code_block
                if in_code_block:
                    if self.style == "github":
                        result.append('<span font_family="monospace" background="#f6f8fa">')
                    elif self.style == "gitlab":
                        result.append('<span font_family="monospace" background="#fdf6e3">')
                    else:
                        result.append('<span font_family="monospace" background="#e3e3e3">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format(stripped_line[2:])
                if self.style == "github":
                    result.append(f'<span size="26000" weight="bold">{processed}</span>')
                elif self.style == "gitlab":
                    result.append(f'<span size="25000" weight="bold" foreground="#1f883d">{processed}</span>')
                else:
                    result.append(f'<span size="24000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format(stripped_line[3:])
                if self.style == "github":
                    result.append(f'<span size="22000" weight="bold">{processed}</span>')
                elif self.style == "gitlab":
                    result.append(f'<span size="21000" weight="bold" foreground="#0969da">{processed}</span>')
                else:
                    result.append(f'<span size="20000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format(stripped_line[4:])
                size = "20000" if self.style == "github" else "19000" if self.style == "gitlab" else "18000"
                result.append(f'<span size="{size}" weight="bold">{processed}</span>')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format(stripped_line[5:])
                size = "18000" if self.style == "github" else "17000" if self.style == "gitlab" else "16000"
                result.append(f'<span size="{size}" weight="bold">{processed}</span>')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format(stripped_line[6:])
                size = "16000" if self.style == "github" else "15000" if self.style == "gitlab" else "14000"
                result.append(f'<span size="{size}" weight="bold">{processed}</span>')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format(stripped_line[7:])
                size = "14000" if self.style == "github" else "13000" if self.style == "gitlab" else "12000"
                result.append(f'<span size="{size}" weight="bold">{processed}</span>')
            elif re.match(r'^[\s]*[-*+]\s+', original_line):
                match = re.match(r'^(\s*)([-*+])\s+(.*)', original_line)
                if match:
                    indent_text, bullet, content = match.groups()
                    
                    if content.startswith('[ ]'):
                        task_content = self._process_inline_format(content[3:].strip())
                        result.append(f'{indent_text}☐ {task_content}')
                    elif content.startswith('[x]') or content.startswith('[X]'):
                        task_content = self._process_inline_format(content[3:].strip())
                        result.append(f'{indent_text}☑ <s>{task_content}</s>')
                    else:
                        processed_content = self._process_inline_format(content)
                        result.append(f'{indent_text}• {processed_content}')
            elif re.match(r'^[\s]*\d+\.\s+', original_line):
                match = re.match(r'^(\s*)(\d+\.)\s+(.*)', original_line)
                if match:
                    indent_text, number, content = match.groups()
                    processed_content = self._process_inline_format(content)
                    result.append(f'{indent_text}{number} {processed_content}')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format(stripped_line[2:])
                if self.style == "github":
                    result.append(f'<span style="italic" foreground="#656d76">▌ {processed}</span>')
                elif self.style == "gitlab":
                    result.append(f'<span style="italic" foreground="#6a737d">│ {processed}</span>')
                else:
                    result.append(f'<span style="italic" foreground="#666666">" {processed} "</span>')
            elif stripped_line.strip() == '---':
                if self.style == "github":
                    result.append('─' * 50)
                elif self.style == "gitlab":
                    result.append('<span foreground="#e1e4e8">' + '─' * 50 + '</span>')
                else:
                    result.append('─' * 50)
            else:
                if stripped_line:
                    processed = self._process_inline_format(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        return '\n'.join(result)
    
    def _process_inline_format(self, text):
        if not text:
            return text
            
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<b>\1</b>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', processed)
        
        if self.style == "github":
            processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="monospace" background="#f6f8fa" foreground="#d1242f">\1</span>', processed)
        elif self.style == "gitlab":
            processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="monospace" background="#fdf6e3" foreground="#bf616a">\1</span>', processed)
        else:
            processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="monospace" background="#e0e0e0">\1</span>', processed)
        
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        
        if self.style == "github":
            processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#0969da" underline="single">\1</span>', processed)
        elif self.style == "gitlab":
            processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#1068bf" underline="single">\1</span>', processed)
        else:
            processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="blue" underline="single">\1</span>', processed)
        
        return processed

def create_icon_from_data_uri(data_uri, size=16):
    """Crea un Gtk.Image desde una data URI (PNG o SVG)"""
    try:
        if data_uri.startswith('data:image/png;base64,'):
            base64_data = data_uri.split(',')[1]
            png_data = base64.b64decode(base64_data)
            
            loader = GdkPixbuf.PixbufLoader.new_with_type('png')
            loader.write(png_data)
            loader.close()
            
            pixbuf = loader.get_pixbuf()
            pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
            
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            image.set_pixel_size(size)
            image.set_size_request(size, size)
            return image
            
        elif data_uri.startswith('data:image/svg+xml;base64,'):
            base64_data = data_uri.split(',')[1]
            svg_content = base64.b64decode(base64_data).decode('utf-8')
            
            loader = GdkPixbuf.PixbufLoader.new_with_type('svg')
            loader.set_size(size, size)
            loader.write(svg_content.encode('utf-8'))
            loader.close()
            
            pixbuf = loader.get_pixbuf()
            pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
            
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            image.set_pixel_size(size)
            image.set_size_request(size, size)
            return image
            
    except Exception as e:
        print(f"Error cargando data URI: {e}")
        
    image = Gtk.Image.new_from_icon_name("view-grid-symbolic")
    image.set_pixel_size(size)
    return image

def create_icon_from_png_file(png_path, size=16):
    """Crea un Gtk.Image desde un archivo PNG"""
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(png_path, size, size)
        
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_pixel_size(size)
        image.set_size_request(size, size)
        return image
        
    except Exception as e:
        print(f"Error cargando PNG desde {png_path}: {e}")
        image = Gtk.Image.new_from_icon_name("view-grid-symbolic")
        image.set_pixel_size(size)
        return image

class MarkdownEditorWindow(Gtk.ApplicationWindow):
    
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            
            self.config = Config()
            self.current_file = None
            self.document_modified = False
            
            # Variables para búsqueda
            self.search_matches = []
            self.current_search_index = -1
            self.search_tag = None
            self.current_search_tag = None
            
            # Renderer con estilo configurable
            render_style = self.config.get("render_style", "default")
            self.renderer = ImprovedRenderer(render_style)
            
            self.set_title("Editor de Markdown")
            self.set_default_size(1000, 700)
            
            # Aplicar tema
            self.apply_theme()
            
            self.setup_ui()
            self.setup_shortcuts()
            self.connect("close-request", self.on_close)
            
        except Exception as e:
            traceback.print_exc()
            raise

    def apply_theme(self):
        """Aplicar tema claro/oscuro"""
        try:
            style_manager = Adw.StyleManager.get_default()
            dark_theme = self.config.get("dark_theme", False)
            if dark_theme:
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            else:
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        except Exception:
            pass

    def setup_ui(self):
        try:
            header_bar = Gtk.HeaderBar()
            header_bar.set_title_widget(Gtk.Label(label="Editor de Markdown"))
            
            # Botones del lado izquierdo
            new_btn = Gtk.Button()
            new_btn.set_icon_name("document-new-symbolic")
            new_btn.set_tooltip_text("Nuevo documento (Ctrl+N)")
            new_btn.connect("clicked", self.on_new)
            header_bar.pack_start(new_btn)
            
            open_btn = Gtk.Button()
            open_btn.set_icon_name("document-open-symbolic")
            open_btn.set_tooltip_text("Abrir archivo (Ctrl+O)")
            open_btn.connect("clicked", self.on_open)
            header_bar.pack_start(open_btn)
            
            self.save_btn = Gtk.Button()
            self.save_btn.set_icon_name("document-save-symbolic")
            self.save_btn.set_tooltip_text("Guardar archivo (Ctrl+S)")
            self.save_btn.connect("clicked", self.on_save)
            self.save_btn.set_sensitive(False)
            header_bar.pack_start(self.save_btn)
            
            # Botón de búsqueda
            search_btn = Gtk.Button()
            search_btn.set_icon_name("system-search-symbolic")
            search_btn.set_tooltip_text("Buscar (Ctrl+F)")
            search_btn.connect("clicked", self.on_search_clicked)
            header_bar.pack_start(search_btn)
            
            # Botón de menú de aplicación (lado derecho)
            menu_button = Gtk.MenuButton()
            menu_button.set_icon_name("open-menu-symbolic")
            menu_button.set_tooltip_text("Menú de aplicación")
            
            # Crear menú
            menu_model = Gio.Menu()
            main_section = Gio.Menu()
            main_section.append("Imprimir...", "app.print")
            menu_model.append_section(None, main_section)
            
            language_menu = Gio.Menu()
            language_menu.append("Auto-detectar", "app.language::auto")
            language_menu.append("English", "app.language::en")
            language_menu.append("Español", "app.language::es")
            menu_model.append_submenu("Idioma", language_menu)
            
            menu_model.append("Preferencias", "app.preferences")
            menu_model.append("Acerca de", "app.about")
            
            menu_button.set_menu_model(menu_model)
            header_bar.pack_end(menu_button)
            
            self.set_titlebar(header_bar)
            
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            
            toolbar_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            toolbar_container.add_css_class("toolbar")
            toolbar_container.set_margin_start(8)
            toolbar_container.set_margin_end(8)
            toolbar_container.set_margin_top(4)
            toolbar_container.set_margin_bottom(4)
            
            toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            toolbar.set_spacing(0)
            toolbar.set_halign(Gtk.Align.START)
            toolbar.set_hexpand(False)
            
            def create_icon_button(icon_name, tooltip, prefix, suffix=""):
                btn = Gtk.Button()
                btn.set_icon_name(icon_name)
                btn.set_tooltip_text(tooltip)
                btn.add_css_class("flat")
                btn.add_css_class("super-compact-btn")
                btn.set_size_request(22, 22)
                btn.set_margin_start(0)
                btn.set_margin_end(0)
                btn.connect("clicked", lambda x: self.insert_format(prefix, suffix))
                return btn
            
            def create_icon_button_with_png(png_path, tooltip, prefix, suffix="", size=16):
                btn = Gtk.Button()
                icon_image = create_icon_from_png_file(png_path, size)
                icon_image.set_halign(Gtk.Align.CENTER)
                icon_image.set_valign(Gtk.Align.CENTER)
                btn.set_child(icon_image)
                btn.set_tooltip_text(tooltip)
                btn.add_css_class("flat")
                btn.add_css_class("super-compact-btn")
                btn.add_css_class("png-toolbar-icon")
                btn.set_size_request(22, 22)
                btn.set_margin_start(0)
                btn.set_margin_end(0)
                btn.connect("clicked", lambda x: self.insert_format(prefix, suffix))
                return btn

            def create_view_button_with_png_file(png_path, tooltip, view_mode, size=16):
                btn = Gtk.Button()
                icon_image = create_icon_from_png_file(png_path, size)
                btn.set_child(icon_image)
                icon_image.set_halign(Gtk.Align.CENTER)
                icon_image.set_valign(Gtk.Align.CENTER)
                btn.set_tooltip_text(tooltip)
                btn.add_css_class("super-compact-btn")
                btn.add_css_class("view-button")
                btn.add_css_class("flat")
                btn.set_size_request(22, 22)
                btn.connect("clicked", lambda x: self.set_view_mode(view_mode))
                return btn
            
            def add_separator():
                sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
                sep.set_margin_start(2)
                sep.set_margin_end(2)
                sep.add_css_class("group-separator")
                toolbar.append(sep)
            
            # Botón de negrita con PNG personalizado
            script_dir = os.path.dirname(os.path.abspath(__file__))
            bold_png_path = os.path.join(script_dir, "images", "bold.png")
            bold_btn = create_icon_button_with_png(bold_png_path, "Negrita (Ctrl+B)", "**", "**", 16)
            toolbar.append(bold_btn)
            
            italic_png_path = os.path.join(script_dir, "images", "italic.png")
            italic_btn = create_icon_button_with_png(italic_png_path, "Cursiva (Ctrl+I)", "*", "*", 16)
            toolbar.append(italic_btn)
            
            strikethrough_png_path = os.path.join(script_dir, "images", "strikethrough.png")
            strikethrough_btn = create_icon_button_with_png(strikethrough_png_path, "Tachado", "~~", "~~", 16)
            toolbar.append(strikethrough_btn)
            
            # Dropdown de encabezados
            headers_button = Gtk.MenuButton()
            headers_button.set_tooltip_text("Seleccionar encabezado")
            headers_button.add_css_class("super-compact-btn")
            headers_button.add_css_class("headers-btn")
            headers_button.add_css_class("png-toolbar-icon")
            headers_button.set_size_request(22, 22)
            text_size_png_path = os.path.join(script_dir, "images", "text-size.png")
            headers_icon_image = create_icon_from_png_file(text_size_png_path, 16)
            headers_icon_image.set_halign(Gtk.Align.CENTER)
            headers_icon_image.set_valign(Gtk.Align.CENTER)
            headers_button.set_child(headers_icon_image)
            
            popover = Gtk.Popover()
            popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            popover_box.set_spacing(0)
            
            header_data = [
                ("H1", "# ", 20),
                ("H2", "## ", 20),
                ("H3", "### ", 20),
                ("H4", "#### ", 20),
                ("H5", "##### ", 20),
                ("H6", "###### ", 20)
            ]
            
            for text, prefix, height in header_data:
                btn = Gtk.Button()
                icon_name = f"h-{text[1:].lower()}.png"
                icon_path = os.path.join(script_dir, "images", icon_name)
                header_icon = create_icon_from_png_file(icon_path, 16)
                header_icon.set_halign(Gtk.Align.CENTER)
                header_icon.set_valign(Gtk.Align.CENTER)
                btn.set_child(header_icon)
                btn.add_css_class("header-preview-btn")
                btn.add_css_class(f"header-{text.lower()}")
                btn.set_size_request(-1, height)

                def make_header_callback(prefix_val):
                    return lambda x: (self.insert_format(prefix_val, ""), popover.popdown())

                btn.connect("clicked", make_header_callback(prefix))
                popover_box.append(btn)
            
            popover.set_child(popover_box)
            headers_button.set_popover(popover)
            toolbar.append(headers_button)
            
            add_separator()
            
            # Botones de listas
            unordered_list_btn = create_icon_button("view-list-symbolic", "Lista con viñetas", "", "")
            unordered_list_btn.connect("clicked", lambda x: self.insert_list_item("unordered"))
            toolbar.append(unordered_list_btn)
            
            ordered_list_btn = create_icon_button("format-ordered-list-symbolic", "Lista numerada", "", "")
            ordered_list_btn.connect("clicked", lambda x: self.insert_list_item("ordered"))
            toolbar.append(ordered_list_btn)
            
            checklist_btn = create_icon_button("object-select-symbolic", "Lista de tareas", "", "")
            checklist_btn.connect("clicked", lambda x: self.insert_list_item("task"))
            toolbar.append(checklist_btn)
            
            quote_btn = create_icon_button("format-quote-close-symbolic", "Cita", "> ", "")
            toolbar.append(quote_btn)
            
            add_separator()
            
            code_inline_btn = create_icon_button("preferences-other-symbolic", "Código en línea", "`", "`")
            toolbar.append(code_inline_btn)

            code_block_btn = create_icon_button("text-plain-symbolic", "Bloque de código", "```\n", "\n```")
            toolbar.append(code_block_btn)
            
            add_separator()
            
            link_btn = create_icon_button("insert-link-symbolic", "Insertar enlace (Ctrl+K)", "[", "](https://ejemplo.com)")
            toolbar.append(link_btn)
            
            image_btn = create_icon_button("insert-image-symbolic", "Insertar imagen", "![", "](imagen.png)")
            toolbar.append(image_btn)
            
            table_btn = create_icon_button("insert-table-symbolic", "Insertar tabla", "", "")
            table_btn.connect("clicked", self.insert_table)
            toolbar.append(table_btn)
            
            add_separator()
            
            hr_btn = create_icon_button("insert-horizontal-rule-symbolic", "Línea horizontal", "\n---\n", "")
            toolbar.append(hr_btn)
            
            add_separator()
            
            toolbar_container.append(toolbar)
            
            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            toolbar_container.append(spacer)
            
            # Botones de vista
            view_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            view_buttons_box.set_spacing(0)
            
            self.split_view_btn = Gtk.Button()
            self.split_view_btn.set_icon_name("layout-columns-symbolic")
            self.split_view_btn.set_tooltip_text("Vista partida (Editor + Vista previa)")
            self.split_view_btn.add_css_class("super-compact-btn")
            self.split_view_btn.add_css_class("view-button")
            self.split_view_btn.add_css_class("flat")
            self.split_view_btn.set_size_request(22, 22)
            self.split_view_btn.connect("clicked", lambda x: self.set_view_mode("split"))
            view_buttons_box.append(self.split_view_btn)
            
            self.editor_view_btn = Gtk.Button()
            self.editor_view_btn.set_icon_name("text-editor-symbolic")
            self.editor_view_btn.set_tooltip_text("Solo editor")
            self.editor_view_btn.add_css_class("super-compact-btn")
            self.editor_view_btn.add_css_class("view-button")
            self.editor_view_btn.add_css_class("flat")
            self.editor_view_btn.add_css_class("view-btn-active")
            self.editor_view_btn.set_size_request(22, 22)
            self.editor_view_btn.connect("clicked", lambda x: self.set_view_mode("editor"))
            view_buttons_box.append(self.editor_view_btn)
            
            self.preview_view_btn = Gtk.Button()
            self.preview_view_btn.set_icon_name("view-paged-symbolic")
            self.preview_view_btn.set_tooltip_text("Solo vista previa")
            self.preview_view_btn.add_css_class("super-compact-btn")
            self.preview_view_btn.add_css_class("view-button")
            self.preview_view_btn.add_css_class("flat")
            self.preview_view_btn.set_size_request(22, 22)
            self.preview_view_btn.connect("clicked", lambda x: self.set_view_mode("preview"))
            view_buttons_box.append(self.preview_view_btn)
            
            toolbar_container.append(view_buttons_box)
            
            main_box.append(toolbar_container)
            
            self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
            self.paned.set_vexpand(True)
            self.paned.set_hexpand(True)
            
            self.current_view_mode = "split"
            
            editor_scroll = Gtk.ScrolledWindow()
            editor_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            self.text_view = Gtk.TextView()
            self.text_view.set_monospace(True)
            self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
            self.text_view.set_left_margin(20)
            self.text_view.set_right_margin(20)
            self.text_view.set_top_margin(15)
            self.text_view.set_bottom_margin(15)
            
            self.text_buffer = self.text_view.get_buffer()
            self.text_buffer.connect("changed", self.on_text_changed)
            
            # Crear tags para búsqueda
            self.search_tag = self.text_buffer.create_tag("search_highlight")
            self.search_tag.set_property("background", "#ffff00")
            self.search_tag.set_property("weight", Pango.Weight.BOLD)

            self.current_search_tag = self.text_buffer.create_tag("current_search_highlight")
            self.current_search_tag.set_property("background", "#ff6600")
            self.current_search_tag.set_property("weight", Pango.Weight.BOLD)
            
            key_controller = Gtk.EventControllerKey()
            key_controller.connect("key-pressed", self.on_key_pressed)
            self.text_view.add_controller(key_controller)
            
            click_controller = Gtk.GestureClick()
            click_controller.connect("pressed", self.on_text_clicked)
            self.text_view.add_controller(click_controller)
            
            self.in_list_context = False
            
            editor_scroll.set_child(self.text_view)
            self.paned.set_start_child(editor_scroll)
            
            preview_scroll = Gtk.ScrolledWindow()
            preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            self.preview_label = Gtk.Label()
            self.preview_label.set_wrap(True)
            self.preview_label.set_wrap_mode(Pango.WrapMode.WORD)
            self.preview_label.set_xalign(0)
            self.preview_label.set_yalign(0)
            self.preview_label.set_margin_start(25)
            self.preview_label.set_margin_end(25)
            self.preview_label.set_margin_top(20)
            self.preview_label.set_margin_bottom(20)
            self.preview_label.set_selectable(True)
            
            preview_scroll.set_child(self.preview_label)
            self.paned.set_end_child(preview_scroll)
            
            self.paned.set_position(500)
            main_box.append(self.paned)
            
            # Barra de búsqueda (inicialmente oculta)
            self.search_bar = self.create_search_bar()
            main_box.append(self.search_bar)
            
            # Barra de estado
            status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            status_box.add_css_class("toolbar")
            status_box.set_spacing(8)
            status_box.set_margin_start(15)
            status_box.set_margin_end(15)
            status_box.set_margin_top(3)
            status_box.set_margin_bottom(3)
            
            self.doc_status_label = Gtk.Label()
            self.doc_status_label.set_text("Listo")
            self.doc_status_label.add_css_class("dim-label")
            status_box.append(self.doc_status_label)
            
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
            
            self.lines_label = Gtk.Label()
            self.lines_label.set_text("1 líneas")
            self.lines_label.add_css_class("dim-label")
            status_box.append(self.lines_label)
            
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
            
            self.words_label = Gtk.Label()
            self.words_label.set_text("0 palabras")
            self.words_label.add_css_class("dim-label")
            status_box.append(self.words_label)
            
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
            
            self.size_label = Gtk.Label()
            self.size_label.set_text("0 B")
            self.size_label.add_css_class("dim-label")
            status_box.append(self.size_label)
            
            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            status_box.append(spacer)
            
            self.cursor_label = Gtk.Label()
            self.cursor_label.set_text("Ln 1, Col 1")
            self.cursor_label.add_css_class("dim-label")
            status_box.append(self.cursor_label)
            
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
            
            self.filetype_label = Gtk.Label()
            self.filetype_label.set_text("Markdown")
            self.filetype_label.add_css_class("dim-label")
            status_box.append(self.filetype_label)
            
            main_box.append(status_box)
            
            self.apply_css()
            self.set_child(main_box)
            
            initial_content = """# Editor de Markdown Mejorado

¡Tu editor está **funcionando perfectamente** con todas las mejoras implementadas!

## Nuevas características

### Búsqueda integrada
- Presiona **Ctrl+F** para buscar en el contenido
- Navega entre resultados con los botones de navegación
- La búsqueda funciona en ambos paneles (editor y vista previa)

### Configuración personalizable
- **Idioma**: Cambia el idioma de la interfaz
- **Tema**: Alterna entre modo claro y oscuro
- **Estilos de renderizado**: Elige entre Default, GitHub y GitLab

### Renderizado mejorado
El visualizador ahora muestra correctamente:
- **Encabezados** con tamaños apropiados
- *Cursiva* y **negrita** perfectamente
- `Código en línea` con fondo
- ~~Texto tachado~~

## Estilos de renderizado disponibles

### Default (Actual)
El estilo clásico y limpio que has estado usando.

### GitHub
Replica los colores y estilos de GitHub:
- Enlaces en azul GitHub (#0969da)
- Código con fondo gris claro
- Encabezados con tamaños específicos

### GitLab
Imita el estilo de GitLab:
- H1 en verde GitLab (#1f883d)
- H2 en azul GitLab (#0969da)
- Código con fondo crema

## Ejemplos de renderizado

### Listas funcionan perfectamente:
1. **Lista numerada**
2. Segundo elemento con *cursiva*
   - Sublista no ordenada
   - Otro elemento con `código`
3. Tercer elemento

### Lista de tareas:
- [x] Implementar búsqueda
- [x] Añadir configuración
- [x] Estilos de renderizado
- [ ] Seguir mejorando

### Citas se ven geniales:
> Esta es una cita que ahora se renderiza correctamente con diferentes estilos según la configuración.

### Código en línea y bloques:

Código en línea: `print("¡Hola mundo!")`

```python
def ejemplo():
    print("Los bloques de código")
    print("se adaptan al estilo seleccionado")
    return "¡Perfectamente!"
```

### Enlaces e imágenes:
- [Enlace de ejemplo](https://ejemplo.com) - Se colorea según el estilo
- ![Imagen de ejemplo](imagen.png)

---

## ¡Todo funciona!

**Prueba las nuevas funciones:**

1. **Ctrl+F** para buscar texto
2. **Menú de configuración** (tres puntos) para cambiar preferencias
3. **Estilos de renderizado** para ver diferentes visualizaciones

*¡Disfruta escribiendo en Markdown!*
"""
            self.text_buffer.set_text(initial_content)
            
        except Exception as e:
            traceback.print_exc()
            raise

    def create_search_bar(self):
        """Crear la barra de búsqueda"""
        search_bar = Gtk.SearchBar()

        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        search_box.set_spacing(6)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(6)
        search_box.set_margin_bottom(6)

        # Entry de búsqueda
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text("Buscar en el documento...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.append(self.search_entry)

        # Botones de navegación
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        nav_box.add_css_class("linked")

        self.prev_button = Gtk.Button()
        self.prev_button.set_icon_name("go-up-symbolic")
        self.prev_button.set_tooltip_text("Anterior")
        self.prev_button.connect("clicked", self.on_search_previous)
        nav_box.append(self.prev_button)

        self.next_button = Gtk.Button()
        self.next_button.set_icon_name("go-down-symbolic")
        self.next_button.set_tooltip_text("Siguiente")
        self.next_button.connect("clicked", self.on_search_next)
        nav_box.append(self.next_button)

        search_box.append(nav_box)

        # Contador de resultados
        self.search_results_label = Gtk.Label()
        self.search_results_label.add_css_class("dim-label")
        self.search_results_label.set_margin_start(12)
        search_box.append(self.search_results_label)

        search_bar.set_child(search_box)
        search_bar.connect_entry(self.search_entry)

        return search_bar

    def apply_css(self):
        """Aplicar estilos CSS"""
        css_provider = Gtk.CssProvider()
        css_data = """
        .super-compact-btn {
            min-height: 22px;
            min-width: 22px;
            margin: 0px;
            border-radius: 2px;
            transition: all 80ms ease-in-out;
            font-size: 9px;
            font-weight: normal;
            border: none;
            box-shadow: none;
            padding: 1px;
            background: transparent;
        }
        
        .super-compact-btn:hover {
            background-color: alpha(@accent_color, 0.15);
            border: none;
            box-shadow: none;
        }
        
        .super-compact-btn:active {
            background-color: alpha(@accent_color, 0.3);
            border: none;
            box-shadow: none;
        }
        
        .headers-btn {
            font-family: serif;
            font-weight: bold;
            font-size: 14px;
            min-width: 22px;
            max-width: 22px;
            min-height: 22px;
            padding: 0px;
            margin: 0px;
        }
        
        .header-preview-btn {
            padding: 0px 2px;
            margin: 0px;
            border-radius: 1px;
            text-align: left;
            min-height: 20px;
            border: none;
            background: transparent;
        }
        
        .header-preview-btn:hover {
            background-color: alpha(@accent_color, 0.1);
        }
        
        .view-button {
            font-family: monospace;
            font-size: 12px;
            font-weight: bold;
            min-width: 22px;
            max-width: 22px;
            min-height: 22px;
            padding: 0px;
            margin: 0px;
            border-radius: 2px;
            transition: all 80ms ease-in-out;
            background: transparent;
            border: none;
        }
        
        .view-btn-active {
            background-color: alpha(@accent_color, 0.15);
            border: none;
            color: @accent_color;
        }
        
        .group-separator {
            margin: 2px 2px;
            opacity: 0.4;
            min-width: 1px;
            min-height: 18px;
            background: alpha(@borders, 0.5);
        }
        
        .toolbar {
            background: alpha(@headerbar_bg_color, 0.98);
            border: none;
            box-shadow: none;
            padding: 1px 0px;
        }
        
        .dim-label {
            opacity: 0.75;
            font-size: 12px;
            font-family: monospace;
            padding: 2px 4px;
            border: none;
            background: transparent;
        }
        
        textview {
            font-family: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.5;
            padding: 0px;
        }
        """
        
        css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_search_clicked(self, button):
        """Mostrar/ocultar barra de búsqueda"""
        is_active = not self.search_bar.get_search_mode()
        self.search_bar.set_search_mode(is_active)
        if is_active:
            self.search_entry.grab_focus()

    def on_search_changed(self, entry):
        """Manejar cambio en la búsqueda"""
        search_text = entry.get_text()
        if search_text:
            self.perform_search(search_text)
        else:
            self.clear_search_highlights()

    def perform_search(self, search_text):
        """Realizar búsqueda en el texto"""
        self.clear_search_highlights()
        
        if not search_text:
            return
        
        # Obtener el texto completo
        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()
        text = self.text_buffer.get_text(start_iter, end_iter, False)
        
        # Buscar coincidencias (case-insensitive)
        self.search_matches = []
        search_text_lower = search_text.lower()
        text_lower = text.lower()
        
        start = 0
        while True:
            pos = text_lower.find(search_text_lower, start)
            if pos == -1:
                break
            
            self.search_matches.append((pos, pos + len(search_text)))
            start = pos + 1
        
        # Resaltar todas las coincidencias
        for start_pos, end_pos in self.search_matches:
            start_iter = self.text_buffer.get_iter_at_offset(start_pos)
            end_iter = self.text_buffer.get_iter_at_offset(end_pos)
            self.text_buffer.apply_tag(self.search_tag, start_iter, end_iter)
        
        # Ir a la primera coincidencia
        if self.search_matches:
            self.current_search_index = 0
            self.highlight_current_match()
            self.update_search_results_label()
        else:
            self.search_results_label.set_text("No se encontraron resultados")

    def clear_search_highlights(self):
        """Limpiar resaltados de búsqueda"""
        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.remove_tag(self.search_tag, start_iter, end_iter)
        self.text_buffer.remove_tag(self.current_search_tag, start_iter, end_iter)
        self.search_matches = []
        self.current_search_index = -1
        self.search_results_label.set_text("")

    def highlight_current_match(self):
        """Resaltar la coincidencia actual"""
        if not self.search_matches or self.current_search_index < 0:
            return
        
        # Limpiar resaltado anterior
        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.remove_tag(self.current_search_tag, start_iter, end_iter)
        
        # Resaltar coincidencia actual
        start_pos, end_pos = self.search_matches[self.current_search_index]
        start_iter = self.text_buffer.get_iter_at_offset(start_pos)
        end_iter = self.text_buffer.get_iter_at_offset(end_pos)
        self.text_buffer.apply_tag(self.current_search_tag, start_iter, end_iter)
        
        # Hacer scroll a la coincidencia
        mark = self.text_buffer.create_mark(None, start_iter, False)
        self.text_view.scroll_to_mark(mark, 0.0, True, 0.0, 0.3)

    def update_search_results_label(self):
        """Actualizar etiqueta de resultados de búsqueda"""
        if self.search_matches:
            current = self.current_search_index + 1
            total = len(self.search_matches)
            self.search_results_label.set_text(f"{current} de {total}")
        else:
            self.search_results_label.set_text("")

    def on_search_next(self, button):
        """Ir a la siguiente coincidencia"""
        if not self.search_matches:
            return
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_matches)
        self.highlight_current_match()
        self.update_search_results_label()

    def on_search_previous(self, button):
        """Ir a la coincidencia anterior"""
        if not self.search_matches:
            return
        
        self.current_search_index = (self.current_search_index - 1) % len(self.search_matches)
        self.highlight_current_match()
        self.update_search_results_label()
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado"""
        try:
            controller = Gtk.ShortcutController()
            
            shortcuts = [
                ("<Control>b", lambda *args: self.insert_format("**", "**")),
                ("<Control>i", lambda *args: self.insert_format("*", "*")),
                ("<Control>k", lambda *args: self.insert_format("[", "](https://)")),
                ("<Control>n", lambda *args: self.on_new(None)),
                ("<Control>o", lambda *args: self.on_open(None)),
                ("<Control>s", lambda *args: self.on_save(None)),
                ("<Control>f", lambda *args: self.toggle_search()),
                ("<Control>1", lambda *args: self.insert_format("# ", "")),
                ("<Control>2", lambda *args: self.insert_format("## ", "")),
                ("<Control>3", lambda *args: self.insert_format("### ", "")),
                ("<Control>4", lambda *args: self.insert_format("#### ", "")),
                ("<Control>5", lambda *args: self.insert_format("##### ", "")),
                ("<Control>6", lambda *args: self.insert_format("###### ", "")),
                ("<Control><Shift>l", lambda *args: self.insert_format("- ", "")),
                ("<Control><Shift>o", lambda *args: self.insert_format("1. ", "")),
                ("<Control><Shift>q", lambda *args: self.insert_format("> ", "")),
                ("<Control><Shift>c", lambda *args: self.insert_format("`", "`")),
                ("<Control><Shift>x", lambda *args: self.insert_format("~~", "~~")),
            ]
            
            for trigger_string, callback in shortcuts:
                shortcut = Gtk.Shortcut()
                shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string(trigger_string))
                shortcut.set_action(Gtk.CallbackAction.new(callback))
                controller.add_shortcut(shortcut)
            
            self.add_controller(controller)
            
        except Exception as e:
            pass

    def toggle_search(self):
        """Alternar búsqueda"""
        if hasattr(self, 'search_bar'):
            is_active = not self.search_bar.get_search_mode()
            self.search_bar.set_search_mode(is_active)
            if is_active:
                self.search_entry.grab_focus()
        return True
    
    def insert_list_item(self, list_type):
        try:
            mark = self.text_buffer.get_insert()
            iter_at_mark = self.text_buffer.get_iter_at_mark(mark)
            
            iter_at_mark.set_line_offset(0)
            self.text_buffer.place_cursor(iter_at_mark)
            
            if list_type == "unordered":
                text = "- List item\n"
            elif list_type == "ordered":
                text = "1. List item\n"
            elif list_type == "task":
                text = "- [ ] List item\n"
            
            self.text_buffer.insert_at_cursor(text)
            self.in_list_context = True
            
        except Exception as e:
            pass
    
    def on_key_pressed(self, controller, keyval, keycode, state):
        try:
            if keyval == Gdk.KEY_Return or keyval == Gdk.KEY_KP_Enter:
                return self.handle_enter_key()
            
            elif keyval in [Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right]:
                GLib.idle_add(self.check_list_context)
            
        return False

        except Exception as e:
            return False
    
    def handle_enter_key(self):
        try:
            if not self.in_list_context:
                return False
            
            mark = self.text_buffer.get_insert()
            iter_at_mark = self.text_buffer.get_iter_at_mark(mark)
            
            line_start = iter_at_mark.copy()
            line_start.set_line_offset(0)
            line_end = iter_at_mark.copy()
            line_end.forward_to_line_end()
            
            current_line = self.text_buffer.get_text(line_start, line_end, False)
            
            list_continuation = None
            
            if re.match(r'^(\s*)[-*+]\s+(?!\[)', current_line):
                match = re.match(r'^(\s*)[-*+]\s+(.*)', current_line)
                if match:
                    indent, content = match.groups()
                    if content.strip():
                        list_continuation = f"{indent}- List item"
                    else:
                        self.in_list_context = False
                        return False
            
            elif re.match(r'^(\s*)\d+\.\s+', current_line):
                match = re.match(r'^(\s*)(\d+)\.\s+(.*)', current_line)
                if match:
                    indent, number, content = match.groups()
                    if content.strip():
                        next_number = int(number) + 1
                        list_continuation = f"{indent}{next_number}. List item"
                    else:
                        self.in_list_context = False
                        return False
            
            elif re.match(r'^(\s*)[-*+]\s+\[\s?\]\s*', current_line):
                match = re.match(r'^(\s*)[-*+]\s+\[\s?\]\s*(.*)', current_line)
                if match:
                    indent, content = match.groups()
                    if content.strip():
                        list_continuation = f"{indent}- [ ] List item"
                    else:
                        self.in_list_context = False
                        return False
            
            else:
                self.in_list_context = False
                return False
            
            if list_continuation:
                self.text_buffer.insert_at_cursor(f"\n{list_continuation}")
                return True
            
            return False
            
        except Exception as e:
            return False
    
    def on_text_clicked(self, gesture, n_press, x, y):
        try:
            GLib.idle_add(self.check_list_context)
    except Exception as e:
            pass

    def check_list_context(self):
        try:
            mark = self.text_buffer.get_insert()
            iter_at_mark = self.text_buffer.get_iter_at_mark(mark)
            
            line_start = iter_at_mark.copy()
            line_start.set_line_offset(0)
            line_end = iter_at_mark.copy()
            line_end.forward_to_line_end()
            
            current_line = self.text_buffer.get_text(line_start, line_end, False)
            
            is_list_line = (
                re.match(r'^(\s*)[-*+]\s+', current_line) or
                re.match(r'^(\s*)\d+\.\s+', current_line) or
                re.match(r'^(\s*)[-*+]\s+\[\s?\]\s*', current_line)
            )
            
            if not is_list_line:
                self.in_list_context = False
            
            return False
            
        except Exception as e:
            return False

    def set_view_mode(self, mode):
        try:
            self.split_view_btn.remove_css_class("view-btn-active")
            self.editor_view_btn.remove_css_class("view-btn-active")
            self.preview_view_btn.remove_css_class("view-btn-active")
            
            editor_widget = self.paned.get_start_child()
            preview_widget = self.paned.get_end_child()
            
            if mode == "split":
                if editor_widget:
                    editor_widget.set_visible(True)
                if preview_widget:
                    preview_widget.set_visible(True)
                self.paned.set_position(500)
                self.split_view_btn.add_css_class("view-btn-active")
                
            elif mode == "editor":
                if editor_widget:
                    editor_widget.set_visible(True)
                if preview_widget:
                    preview_widget.set_visible(False)
                self.editor_view_btn.add_css_class("view-btn-active")
                
            elif mode == "preview":
                if editor_widget:
                    editor_widget.set_visible(False)
                if preview_widget:
                    preview_widget.set_visible(True)
                self.preview_view_btn.add_css_class("view-btn-active")
            
            self.current_view_mode = mode
            
        except Exception as e:
            pass

    def insert_table(self, button):
        try:
            table_text = """| Encabezado 1 | Encabezado 2 | Encabezado 3 |
|--------------|--------------|--------------|
| Celda 1      | Celda 2      | Celda 3      |
| Celda 4      | Celda 5      | Celda 6      |
"""
            self.text_buffer.insert_at_cursor(table_text)
        except Exception as e:
            pass
    
    def update_cursor_position(self):
        try:
            mark = self.text_buffer.get_insert()
            iter_at_mark = self.text_buffer.get_iter_at_mark(mark)
            line = iter_at_mark.get_line() + 1
            col = iter_at_mark.get_line_offset() + 1
            self.cursor_label.set_text(f"Ln {line}, Col {col}")
        except Exception as e:
            pass
    
    def update_detailed_stats(self, text):
        try:
            lines = text.split('\n')
            words = len([word for word in text.split() if word.strip()])
            size_bytes = len(text.encode('utf-8'))
            
            self.lines_label.set_text(f"{len(lines)} líneas")
            self.words_label.set_text(f"{words} palabras")
            
            if size_bytes < 1024:
                size_text = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_text = f"{size_bytes / 1024:.1f} KB"
    else:
                size_text = f"{size_bytes / (1024 * 1024):.1f} MB"
            
            self.size_label.set_text(size_text)
            self.update_cursor_position()
            
        except Exception as e:
            pass
    
    def insert_format(self, prefix, suffix=""):
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
            pass
    
    def on_text_changed(self, buffer):
        try:
            self.document_modified = True
            self.save_btn.set_sensitive(True)
            
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            
            preview_text = self.renderer.render_text(text)
            
            try:
                self.preview_label.set_markup(preview_text)
            except Exception:
                self.preview_label.set_text(text)
            
            self.update_detailed_stats(text)
            self.doc_status_label.set_text("Modificado")
            
        except Exception as e:
            pass
    
    def on_new(self, button):
        try:
            content = "# Nuevo Documento\n\nEscribe aquí tu contenido..."
            self.text_buffer.set_text(content)
            self.current_file = None
            self.document_modified = False
            self.save_btn.set_sensitive(False)
            self.set_title("Nuevo documento - Editor de Markdown")
        except Exception as e:
            pass
    
    def on_open(self, button):
        try:
            dialog = Gtk.FileChooserDialog(
                title="Abrir archivo",
                parent=self,
                action=Gtk.FileChooserAction.OPEN
            )
            dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
            dialog.add_button("Abrir", Gtk.ResponseType.ACCEPT)
            
            def on_response(dialog, response):
                if response == Gtk.ResponseType.ACCEPT:
                    file = dialog.get_file()
                    if file:
                        try:
                            with open(file.get_path(), "r", encoding="utf-8") as f:
                                content = f.read()
                            self.text_buffer.set_text(content)
                            self.current_file = file.get_path()
                            self.document_modified = False
                            self.save_btn.set_sensitive(False)
                            filename = os.path.basename(self.current_file)
                            self.set_title(f"{filename} - Editor de Markdown")
                        except Exception as e:
                            pass
                dialog.destroy()
            
            dialog.connect("response", on_response)
            dialog.show()
            
        except Exception as e:
            pass
    
    def on_save(self, button):
        try:
            if not self.current_file:
                dialog = Gtk.FileChooserDialog(
                    title="Guardar archivo",
                    parent=self,
                    action=Gtk.FileChooserAction.SAVE
                )
                dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
                dialog.add_button("Guardar", Gtk.ResponseType.ACCEPT)
                dialog.set_current_name("documento.md")
                
                def on_save_response(dialog, response):
                    if response == Gtk.ResponseType.ACCEPT:
                        file = dialog.get_file()
                        if file:
                            self.current_file = file.get_path()
                            self.save_file()
                    dialog.destroy()
                
                dialog.connect("response", on_save_response)
                dialog.show()
            else:
                self.save_file()
                
        except Exception as e:
            pass
    
    def save_file(self):
        try:
            text = self.text_buffer.get_text(
                self.text_buffer.get_start_iter(),
                self.text_buffer.get_end_iter(),
                False
            )
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(text)
            
            self.document_modified = False
            self.save_btn.set_sensitive(False)
            filename = os.path.basename(self.current_file)
            self.set_title(f"{filename} - Editor de Markdown")
            self.doc_status_label.set_text("Guardado")
            
        except Exception as e:
            pass
    
    def on_close(self, window):
        try:
            self.config.set("paned_position", self.paned.get_position())
            width, height = self.get_default_size()
            self.config.set("window_width", width)
            self.config.set("window_height", height)
        except Exception as e:
            pass
        
        return False

class MarkdownApp(Adw.Application):
    
    def __init__(self):
        try:
            super().__init__(
                application_id="com.example.MarkdownEditor",
                flags=Gio.ApplicationFlags.DEFAULT_FLAGS
            )
            self.connect("activate", self.on_activate)
            self.setup_actions()
        except Exception as e:
            traceback.print_exc()
            raise
    
    def setup_actions(self):
        """Configurar acciones de la aplicación"""
        # Acción de impresión
        print_action = Gio.SimpleAction.new("print", None)
        print_action.connect("activate", self.on_print)
        self.add_action(print_action)
        
        # Acción de cambio de idioma
        language_action = Gio.SimpleAction.new_stateful(
            "language", GLib.VariantType.new("s"), GLib.Variant("s", "auto")
        )
        language_action.connect("activate", self.on_language_changed)
        self.add_action(language_action)
        
        # Acción de preferencias
        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)
        
        # Acción de acerca de
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)

    def on_language_changed(self, action, parameter):
        """Cambiar idioma de la aplicación"""
        language_code = parameter.get_string()
        action.set_state(parameter)
        if hasattr(self, "win"):
            self.win.config.set("language", language_code)

    def on_preferences(self, action, parameter):
        """Mostrar ventana de preferencias"""
        if hasattr(self, "win"):
            self.show_preferences_dialog()

    def show_preferences_dialog(self):
        """Mostrar diálogo de preferencias"""
        dialog = Adw.PreferencesWindow()
        dialog.set_title("Preferencias")
        dialog.set_modal(True)
        dialog.set_transient_for(self.win)

        # Página de preferencias generales
        page = Adw.PreferencesPage()
        page.set_title("General")

        # Grupo de idioma
        language_group = Adw.PreferencesGroup()
        language_group.set_title("Idioma")

        # Selector de idioma
        language_row = Adw.ComboRow()
        language_row.set_title("Idioma de la interfaz")
        language_model = Gtk.StringList()
        language_model.append("Auto-detectar")
        language_model.append("English")
        language_model.append("Español")
        language_row.set_model(language_model)

        # Establecer selección actual
        current_lang = self.win.config.get("language", "auto")
        if current_lang == "auto":
            language_row.set_selected(0)
        elif current_lang == "en":
            language_row.set_selected(1)
        elif current_lang == "es":
            language_row.set_selected(2)

        language_row.connect("notify::selected", self.on_language_row_changed)
        language_group.add(language_row)
        page.add(language_group)

        # Grupo de apariencia
        appearance_group = Adw.PreferencesGroup()
        appearance_group.set_title("Apariencia")

        # Switch para tema oscuro
        dark_theme_row = Adw.SwitchRow()
        dark_theme_row.set_title("Tema oscuro")
        dark_theme_row.set_subtitle("Usar tema oscuro para la aplicación")
        dark_theme_row.set_active(self.win.config.get("dark_theme", False))
        dark_theme_row.connect("notify::active", self.on_theme_changed)
        appearance_group.add(dark_theme_row)

        # Selector de estilo de renderizado
        render_style_row = Adw.ComboRow()
        render_style_row.set_title("Estilo de renderizado")
        render_style_row.set_subtitle("Cambia la apariencia de la vista previa")
        render_style_model = Gtk.StringList()
        render_style_model.append("Default")
        render_style_model.append("GitHub")
        render_style_model.append("GitLab")
        render_style_row.set_model(render_style_model)

        # Establecer selección actual
        current_style = self.win.config.get("render_style", "default")
        if current_style == "default":
            render_style_row.set_selected(0)
        elif current_style == "github":
            render_style_row.set_selected(1)
        elif current_style == "gitlab":
            render_style_row.set_selected(2)

        render_style_row.connect("notify::selected", self.on_render_style_changed)
        appearance_group.add(render_style_row)
        page.add(appearance_group)

        dialog.add(page)
        dialog.present()

    def on_theme_changed(self, switch_row, param):
        """Manejar cambio de tema"""
        dark_theme = switch_row.get_active()
        self.win.config.set("dark_theme", dark_theme)
        self.win.apply_theme()

    def on_render_style_changed(self, combo_row, param):
        """Manejar cambio de estilo de renderizado"""
        selected = combo_row.get_selected()
        styles = ["default", "github", "gitlab"]
        if selected < len(styles):
            style = styles[selected]
            self.win.config.set("render_style", style)
            self.win.renderer.set_style(style)
            # Actualizar vista previa
            if hasattr(self.win, 'text_buffer'):
                self.win.on_text_changed(self.win.text_buffer)

    def on_language_row_changed(self, combo_row, param):
        """Manejar cambio en el selector de idioma"""
        selected = combo_row.get_selected()
        language_codes = ["auto", "en", "es"]
        if selected < len(language_codes):
            language_code = language_codes[selected]
            action = self.lookup_action("language")
            if action:
                action.activate(GLib.Variant("s", language_code))

    def on_print(self, action, parameter):
        """Manejar la acción de imprimir"""
        print("Función de impresión no implementada")

    def on_about(self, action, parameter):
        """Mostrar diálogo Acerca de"""
        about_dialog = Adw.AboutWindow()
        about_dialog.set_transient_for(self.win)
        about_dialog.set_modal(True)
        about_dialog.set_application_name("Editor de Markdown")
        about_dialog.set_version("2.0.0")
        about_dialog.set_developer_name("Desarrollador")
        about_dialog.set_copyright("© 2025")
        about_dialog.set_comments("Un editor de Markdown simple y potente con búsqueda y múltiples estilos de renderizado")
        about_dialog.set_license_type(Gtk.License.GPL_3_0)
        about_dialog.set_developers(["Desarrollador Principal"])
        about_dialog.present()
    
    def on_activate(self, app):
        try:
            self.win = MarkdownEditorWindow(application=app)
            self.win.present()
        except Exception as e:
            traceback.print_exc()

def main():
    try:
        app = MarkdownApp()
        result = app.run(sys.argv)
        return result
        
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
    
    def apply_theme(self):
        """Aplicar tema claro/oscuro"""
        style_manager = Adw.StyleManager.get_default()
        dark_theme = self.config.get("dark_theme", False)
        if dark_theme:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
    
    def setup_ui(self):
        try:
            header_bar = Gtk.HeaderBar()
            header_bar.set_title_widget(Gtk.Label(label="Editor de Markdown"))
            
            # Botones del lado izquierdo
            new_btn = Gtk.Button()
            new_btn.set_icon_name("document-new-symbolic")
            new_btn.set_tooltip_text("Nuevo documento (Ctrl+N)")
            new_btn.connect("clicked", self.on_new)
            header_bar.pack_start(new_btn)
            
            open_btn = Gtk.Button()
            open_btn.set_icon_name("document-open-symbolic")
            open_btn.set_tooltip_text("Abrir archivo (Ctrl+O)")
            open_btn.connect("clicked", self.on_open)
            header_bar.pack_start(open_btn)
            
            self.save_btn = Gtk.Button()
            self.save_btn.set_icon_name("document-save-symbolic")
            self.save_btn.set_tooltip_text("Guardar archivo (Ctrl+S)")
            self.save_btn.connect("clicked", self.on_save)
            self.save_btn.set_sensitive(False)
            header_bar.pack_start(self.save_btn)
            
            # Botón de búsqueda
            search_btn = Gtk.Button()
            search_btn.set_icon_name("system-search-symbolic")
            search_btn.set_tooltip_text("Buscar (Ctrl+F)")
            search_btn.connect("clicked", self.on_search_clicked)
            header_bar.pack_start(search_btn)
            
            # Botón de menú de aplicación (lado derecho)
            menu_button = Gtk.MenuButton()
            menu_button.set_icon_name("open-menu-symbolic")
            menu_button.set_tooltip_text("Menú de aplicación")
            
            # Crear menú
            menu_model = Gio.Menu()
            
            # Sección principal
            main_section = Gio.Menu()
            main_section.append("Imprimir...", "app.print")
            menu_model.append_section(None, main_section)
            
            # Submenú de idioma
            language_menu = Gio.Menu()
            language_menu.append("Auto-detectar", "app.language::auto")
            language_menu.append("English", "app.language::en")
            language_menu.append("Español", "app.language::es")
            menu_model.append_submenu("Idioma", language_menu)
            
            # Elementos adicionales
            menu_model.append("Preferencias", "app.preferences")
            menu_model.append("Acerca de", "app.about")
            
            menu_button.set_menu_model(menu_model)
            header_bar.pack_end(menu_button)
            
            self.set_titlebar(header_bar)
            
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            
            toolbar_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            toolbar_container.add_css_class("toolbar")
            toolbar_container.set_margin_start(8)
            toolbar_container.set_margin_end(8)
            toolbar_container.set_margin_top(4)
            toolbar_container.set_margin_bottom(4)
            
            toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            toolbar.set_spacing(0)
            toolbar.set_halign(Gtk.Align.START)
            toolbar.set_hexpand(False)
            
            def create_icon_button(icon_name, tooltip, prefix, suffix=""):
                btn = Gtk.Button()
                btn.set_icon_name(icon_name)
                btn.set_tooltip_text(tooltip)
                btn.add_css_class("flat")
                btn.add_css_class("super-compact-btn")
                btn.set_size_request(22, 22)
                btn.set_margin_start(0)
                btn.set_margin_end(0)
                btn.connect("clicked", lambda x: self.insert_format(prefix, suffix))
                return btn
            
            def create_icon_button_with_png(png_path, tooltip, prefix, suffix="", size=16):
                btn = Gtk.Button()
                icon_image = create_icon_from_png_file(png_path, size)
                icon_image.set_halign(Gtk.Align.CENTER)
                icon_image.set_valign(Gtk.Align.CENTER)
                btn.set_child(icon_image)
                btn.set_tooltip_text(tooltip)
                btn.add_css_class("flat")
                btn.add_css_class("super-compact-btn")
                btn.add_css_class("png-toolbar-icon")
                btn.set_size_request(22, 22)
                btn.set_margin_start(0)
                btn.set_margin_end(0)
                btn.connect("clicked", lambda x: self.insert_format(prefix, suffix))
                return btn

            def create_view_button_with_png_file(png_path, tooltip, view_mode, size=16):
                """Crear botón de vista con icono PNG desde archivo"""
                btn = Gtk.Button()
                
                icon_image = create_icon_from_png_file(png_path, size)
                btn.set_child(icon_image)
                icon_image.set_halign(Gtk.Align.CENTER)
                icon_image.set_valign(Gtk.Align.CENTER)
                
                btn.set_tooltip_text(tooltip)
                btn.add_css_class("super-compact-btn")
                btn.add_css_class("view-button")
                btn.add_css_class("flat")
                btn.set_size_request(22, 22)
                btn.connect("clicked", lambda x: self.set_view_mode(view_mode))
                return btn
            
            def add_separator():
                sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
                sep.set_margin_start(2)
                sep.set_margin_end(2)
                sep.add_css_class("group-separator")
                toolbar.append(sep)
            
            # Botón de negrita con PNG personalizado
            script_dir = os.path.dirname(os.path.abspath(__file__))
            bold_png_path = os.path.join(script_dir, "images", "bold.png")
            bold_btn = create_icon_button_with_png(bold_png_path, "Negrita (Ctrl+B)", "**", "**", 16)
            toolbar.append(bold_btn)
            
            italic_png_path = os.path.join(script_dir, "images", "italic.png")
            italic_btn = create_icon_button_with_png(italic_png_path, "Cursiva (Ctrl+I)", "*", "*", 16)
            toolbar.append(italic_btn)
            
            strikethrough_png_path = os.path.join(script_dir, "images", "strikethrough.png")
            strikethrough_btn = create_icon_button_with_png(strikethrough_png_path, "Tachado", "~~", "~~", 16)
            toolbar.append(strikethrough_btn)
            
            # Dropdown de encabezados
            headers_button = Gtk.MenuButton()
            headers_button.set_tooltip_text("Seleccionar encabezado")
            headers_button.add_css_class("super-compact-btn")
            headers_button.add_css_class("headers-btn")
            headers_button.add_css_class("png-toolbar-icon")
            headers_button.set_size_request(22, 22)
            text_size_png_path = os.path.join(script_dir, "images", "text-size.png")
            headers_icon_image = create_icon_from_png_file(text_size_png_path, 16)
            headers_icon_image.set_halign(Gtk.Align.CENTER)
            headers_icon_image.set_valign(Gtk.Align.CENTER)
            headers_button.set_child(headers_icon_image)
            
            popover = Gtk.Popover()
            popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            popover_box.set_spacing(0)
            
            header_data = [
                ("H1", "# ", 20),
                ("H2", "## ", 20),
                ("H3", "### ", 20),
                ("H4", "#### ", 20),
                ("H5", "##### ", 20),
                ("H6", "###### ", 20)
            ]
            
            for text, prefix, height in header_data:
                btn = Gtk.Button()
                icon_name = f"h-{text[1:].lower()}.png"
                icon_path = os.path.join(script_dir, "images", icon_name)
                header_icon = create_icon_from_png_file(icon_path, 16)
                header_icon.set_halign(Gtk.Align.CENTER)
                header_icon.set_valign(Gtk.Align.CENTER)
                btn.set_child(header_icon)
                btn.add_css_class("header-preview-btn")
                btn.add_css_class(f"header-{text.lower()}")
                btn.set_size_request(-1, height)

                def make_header_callback(prefix_val):
                    return lambda x: (self.insert_format(prefix_val, ""), popover.popdown())

                btn.connect("clicked", make_header_callback(prefix))
                popover_box.append(btn)
            
            popover.set_child(popover_box)
            headers_button.set_popover(popover)
            toolbar.append(headers_button)
            
            add_separator()
            
            # Botones de listas
            unordered_list_btn = create_icon_button("view-list-symbolic", "Lista con viñetas", "", "")
            unordered_list_btn.connect("clicked", lambda x: self.insert_list_item("unordered"))
            toolbar.append(unordered_list_btn)
            
            ordered_list_btn = create_icon_button("format-ordered-list-symbolic", "Lista numerada", "", "")
            ordered_list_btn.connect("clicked", lambda x: self.insert_list_item("ordered"))
            toolbar.append(ordered_list_btn)
            
            checklist_btn = create_icon_button("object-select-symbolic", "Lista de tareas", "", "")
            checklist_btn.connect("clicked", lambda x: self.insert_list_item("task"))
            toolbar.append(checklist_btn)
            
            quote_btn = create_icon_button("format-quote-close-symbolic", "Cita", "> ", "")
            toolbar.append(quote_btn)
            
            add_separator()
            
            code_inline_btn = create_icon_button("preferences-other-symbolic", "Código en línea", "`", "`")
            toolbar.append(code_inline_btn)

            code_block_btn = create_icon_button("text-plain-symbolic", "Bloque de código", "```\n", "\n```")
            toolbar.append(code_block_btn)
            
            add_separator()
            
            link_btn = create_icon_button("insert-link-symbolic", "Insertar enlace (Ctrl+K)", "[", "](https://ejemplo.com)")
            toolbar.append(link_btn)
            
            image_btn = create_icon_button("insert-image-symbolic", "Insertar imagen", "![", "](imagen.png)")
            toolbar.append(image_btn)
            
            table_btn = create_icon_button("insert-table-symbolic", "Insertar tabla", "", "")
            table_btn.connect("clicked", self.insert_table)
            toolbar.append(table_btn)
            
            add_separator()
            
            hr_btn = create_icon_button("insert-horizontal-rule-symbolic", "Línea horizontal", "\n---\n", "")
            toolbar.append(hr_btn)
            
            add_separator()
            
            toolbar_container.append(toolbar)
            
            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            toolbar_container.append(spacer)
            
            # Botones de vista
            view_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            view_buttons_box.set_spacing(0)
            
            self.split_view_btn = Gtk.Button()
            self.split_view_btn.set_icon_name("layout-columns-symbolic")
            self.split_view_btn.set_tooltip_text("Vista partida (Editor + Vista previa)")
            self.split_view_btn.add_css_class("super-compact-btn")
            self.split_view_btn.add_css_class("view-button")
            self.split_view_btn.add_css_class("flat")
            self.split_view_btn.set_size_request(22, 22)
            self.split_view_btn.connect("clicked", lambda x: self.set_view_mode("split"))
            view_buttons_box.append(self.split_view_btn)
            
            self.editor_view_btn = Gtk.Button()
            self.editor_view_btn.set_icon_name("text-editor-symbolic")
            self.editor_view_btn.set_tooltip_text("Solo editor")
            self.editor_view_btn.add_css_class("super-compact-btn")
            self.editor_view_btn.add_css_class("view-button")
            self.editor_view_btn.add_css_class("flat")
            self.editor_view_btn.add_css_class("view-btn-active")
            self.editor_view_btn.set_size_request(22, 22)
            self.editor_view_btn.connect("clicked", lambda x: self.set_view_mode("editor"))
            view_buttons_box.append(self.editor_view_btn)
            
            self.preview_view_btn = Gtk.Button()
            self.preview_view_btn.set_icon_name("view-paged-symbolic")
            self.preview_view_btn.set_tooltip_text("Solo vista previa")
            self.preview_view_btn.add_css_class("super-compact-btn")
            self.preview_view_btn.add_css_class("view-button")
            self.preview_view_btn.add_css_class("flat")
            self.preview_view_btn.set_size_request(22, 22)
            self.preview_view_btn.connect("clicked", lambda x: self.set_view_mode("preview"))
            view_buttons_box.append(self.preview_view_btn)
            
            toolbar_container.append(view_buttons_box)
            
            main_box.append(toolbar_container)
            
            self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
            self.paned.set_vexpand(True)
            self.paned.set_hexpand(True)
            
            self.current_view_mode = "split"
            
            editor_scroll = Gtk.ScrolledWindow()
            editor_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            self.text_view = Gtk.TextView()
            self.text_view.set_monospace(True)
            self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
            self.text_view.set_left_margin(20)
            self.text_view.set_right_margin(20)
            self.text_view.set_top_margin(15)
            self.text_view.set_bottom_margin(15)
            
            self.text_buffer = self.text_view.get_buffer()
            self.text_buffer.connect("changed", self.on_text_changed)
            
            # Crear tags para búsqueda
            self.search_tag = self.text_buffer.create_tag("search_highlight")
            self.search_tag.set_property("background", "#ffff00")
            self.search_tag.set_property("weight", Pango.Weight.BOLD)

            self.current_search_tag = self.text_buffer.create_tag("current_search_highlight")
            self.current_search_tag.set_property("background", "#ff6600")
            self.current_search_tag.set_property("weight", Pango.Weight.BOLD)
            
            key_controller = Gtk.EventControllerKey()
            key_controller.connect("key-pressed", self.on_key_pressed)
            self.text_view.add_controller(key_controller)
            
            click_controller = Gtk.GestureClick()
            click_controller.connect("pressed", self.on_text_clicked)
            self.text_view.add_controller(click_controller)
            
            self.in_list_context = False
            
            editor_scroll.set_child(self.text_view)
            self.paned.set_start_child(editor_scroll)
            
            preview_scroll = Gtk.ScrolledWindow()
            preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            self.preview_label = Gtk.Label()
            self.preview_label.set_wrap(True)
            self.preview_label.set_wrap_mode(Pango.WrapMode.WORD)
            self.preview_label.set_xalign(0)
            self.preview_label.set_yalign(0)
            self.preview_label.set_margin_start(25)
            self.preview_label.set_margin_end(25)
            self.preview_label.set_margin_top(20)
            self.preview_label.set_margin_bottom(20)
            self.preview_label.set_selectable(True)
            
            preview_scroll.set_child(self.preview_label)
            self.paned.set_end_child(preview_scroll)
            
            self.paned.set_position(500)
            main_box.append(self.paned)
            
            # Barra de búsqueda (inicialmente oculta)
            self.search_bar = self.create_search_bar()
            main_box.append(self.search_bar)
            
            # Barra de estado
            status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            status_box.add_css_class("toolbar")
            status_box.set_spacing(8)
            status_box.set_margin_start(15)
            status_box.set_margin_end(15)
            status_box.set_margin_top(3)
            status_box.set_margin_bottom(3)
            
            self.doc_status_label = Gtk.Label()
            self.doc_status_label.set_text("Listo")
            self.doc_status_label.add_css_class("dim-label")
            status_box.append(self.doc_status_label)
            
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
            
            self.lines_label = Gtk.Label()
            self.lines_label.set_text("1 líneas")
            self.lines_label.add_css_class("dim-label")
            status_box.append(self.lines_label)
            
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
            
            self.words_label = Gtk.Label()
            self.words_label.set_text("0 palabras")
            self.words_label.add_css_class("dim-label")
            status_box.append(self.words_label)
            
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
            
            self.size_label = Gtk.Label()
            self.size_label.set_text("0 B")
            self.size_label.add_css_class("dim-label")
            status_box.append(self.size_label)
            
            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            status_box.append(spacer)
            
            self.cursor_label = Gtk.Label()
            self.cursor_label.set_text("Ln 1, Col 1")
            self.cursor_label.add_css_class("dim-label")
            status_box.append(self.cursor_label)
            
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
            
            self.filetype_label = Gtk.Label()
            self.filetype_label.set_text("Markdown")
            self.filetype_label.add_css_class("dim-label")
            status_box.append(self.filetype_label)
            
            main_box.append(status_box)
            
            self.apply_css()
            self.set_child(main_box)
            
            initial_content = """# Editor de Markdown Mejorado

¡Tu editor está **funcionando perfectamente** con todas las mejoras implementadas!

## Nuevas características

### Búsqueda integrada
- Presiona **Ctrl+F** para buscar en el contenido
- Navega entre resultados con los botones de navegación
- La búsqueda funciona en ambos paneles (editor y vista previa)

### Configuración personalizable
- **Idioma**: Cambia el idioma de la interfaz
- **Tema**: Alterna entre modo claro y oscuro
- **Estilos de renderizado**: Elige entre Default, GitHub y GitLab

### Renderizado mejorado
El visualizador ahora muestra correctamente:
- **Encabezados** con tamaños apropiados
- *Cursiva* y **negrita** perfectamente
- `Código en línea` con fondo
- ~~Texto tachado~~

## Estilos de renderizado disponibles

### Default (Actual)
El estilo clásico y limpio que has estado usando.

### GitHub
Replica los colores y estilos de GitHub:
- Enlaces en azul GitHub (#0969da)
- Código con fondo gris claro
- Encabezados con tamaños específicos

### GitLab
Imita el estilo de GitLab:
- H1 en verde GitLab (#1f883d)
- H2 en azul GitLab (#0969da)
- Código con fondo crema

## Ejemplos de renderizado

### Listas funcionan perfectamente:
1. **Lista numerada**
2. Segundo elemento con *cursiva*
   - Sublista no ordenada
   - Otro elemento con `código`
3. Tercer elemento

### Lista de tareas:
- [x] Implementar búsqueda
- [x] Añadir configuración
- [x] Estilos de renderizado
- [ ] Seguir mejorando

### Citas se ven geniales:
> Esta es una cita que ahora se renderiza correctamente con diferentes estilos según la configuración.

### Código en línea y bloques:

Código en línea: `print("¡Hola mundo!")`

```python
def ejemplo():
    print("Los bloques de código")
    print("se adaptan al estilo seleccionado")
    return "¡Perfectamente!"
```

### Enlaces e imágenes:
- [Enlace de ejemplo](https://ejemplo.com) - Se colorea según el estilo
- ![Imagen de ejemplo](imagen.png)

---

## ¡Todo funciona!

**Prueba las nuevas funciones:**

1. **Ctrl+F** para buscar texto
2. **Menú de configuración** (tres puntos) para cambiar preferencias
3. **Estilos de renderizado** para ver diferentes visualizaciones

*¡Disfruta escribiendo en Markdown!*
"""
            self.text_buffer.set_text(initial_content)
            
        except Exception as e:
            traceback.print_exc()
            raise