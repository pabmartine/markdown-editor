#!/usr/bin/env python3

import sys
import os
import traceback
import re
import json
import locale
import gettext
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Gio, GLib, Pango, Gdk, Adw
except Exception as e:
    print(_("Could not import GTK4 and Adwaita."))
    print(_("Make sure you have python3-gi, libgtk-4-dev and libadwaita-1-dev installed"))
    print(f"{_('Specific error')}: {e}")
    sys.exit(1)

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

# Configuración de internacionalización - Compatible con Flatpak
def get_locale_dir():
    """Obtener directorio de locale apropiado"""
    # Buscar en múltiples ubicaciones
    possible_dirs = [
        "/app/share/locale",  # Ubicación estándar en Flatpak
        os.path.join(os.path.dirname(__file__), "locale"),  # Desarrollo local
        "/usr/share/locale"  # Sistema
    ]
    
    for locale_dir in possible_dirs:
        if os.path.exists(locale_dir):
            return locale_dir
    
    # Fallback al directorio relativo
    return os.path.join(os.path.dirname(__file__), "locale")

LOCALE_DIR = get_locale_dir()
DOMAIN = "markdown-editor"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "markdown-editor")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def setup_locale(language=None):
    """Configurar el idioma de la aplicación - Compatible con Flatpak"""
    if language and language != "auto":
        try:
            os.environ["LANGUAGE"] = language
            os.environ["LC_MESSAGES"] = language
        except:
            pass
    
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        try:
            # Fallback para entornos restringidos como Flatpak
            locale.setlocale(locale.LC_ALL, "C.UTF-8")
        except locale.Error:
            pass
    
    try:
        # Detectar si estamos en Flatpak
        is_flatpak = os.path.exists("/app") or os.environ.get("FLATPAK_ID")
        
        if is_flatpak:
            # En Flatpak, usar directamente /app/share/locale
            locale_dir = "/app/share/locale"
        else:
            locale_dir = LOCALE_DIR
        
        if os.path.exists(locale_dir):
            lang_translations = gettext.translation(DOMAIN, locale_dir, fallback=True)
            lang_translations.install()
            return lang_translations.gettext
        else:
            # Fallback si no hay traducciones
            return lambda text: text
            
    except Exception as e:
        print(f"Warning: Error configurando locale: {e}")
        return lambda text: text

# Configurar idioma inicial
_ = setup_locale()

# Función simple para obtener idiomas disponibles
def get_available_languages():
    """Obtener lista de idiomas disponibles"""
    return [
        ("auto", _("Auto-detect")),
        ("en", _("English")),  
        ("es", _("Spanish"))
    ]

# Función para cambiar idioma dinámicamente
def change_language_global(language_code):
    """Cambiar idioma dinámicamente"""
    global _
    _ = setup_locale(language_code if language_code != "auto" else None)
    return _

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
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading configuration: {e}")
    
    def save_config(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()

class ImprovedRenderer:
    def __init__(self):
        self.style = "default"

    def render_text(self, markdown_text):
        try:
            if MARKDOWN_AVAILABLE:
                extensions = [
                    'tables',
                    'fenced_code',
                    'sane_lists',
                    'nl2br',
                    'smarty',
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
                self.pending_li_content = None

            def flush_pending_li(self):
                if self.pending_li_content:
                    indent, btype = self.pending_li_content
                    bullet = "• " if btype == 'ul' else "1. "
                    
                    if self.style == "github" or self.style == "github-light":
                        bullet = f'<span foreground="#1f2328">{bullet}</span>'
                    elif self.style == "github-dark":
                        bullet = f'<span foreground="#f0f6fc">{bullet}</span>'
                    elif self.style == "gitlab":
                        bullet = f'<span foreground="#303030">{bullet}</span>'
                    elif self.style == "splendor":
                        bullet = f'<span foreground="#2c3e50">{bullet}</span>'
                    elif self.style == "modest":
                        bullet = f'<span foreground="#333">{bullet}</span>'
                    elif self.style == "retro":
                        bullet = f'<span foreground="#8b4513">{bullet}</span>'
                    elif self.style == "air":
                        bullet = f'<span foreground="#268bd2">{bullet}</span>'
                        
                    self.output.append(f'{indent}{bullet}')
                    self.pending_li_content = None

            def handle_starttag(self, tag, attrs):
                if tag != 'li':
                    self.flush_pending_li()
                    
                self.tag_stack.append(tag)
                
                if tag == 'h1':
                    self.in_heading_level = 1
                    if self.style == "github":
                        self.output.append('\n<span size="28000" weight="bold" foreground="#1f2328">')
                    elif self.style == "github-light":
                        self.output.append('\n<span size="32000" weight="600" foreground="#1f2328">')
                    elif self.style == "github-dark":
                        self.output.append('\n<span size="32000" weight="600" foreground="#f0f6fc">')
                    elif self.style == "gitlab":
                        self.output.append('\n<span size="28000" weight="bold" foreground="#303030">')
                    elif self.style == "splendor":
                        self.output.append('\n<span size="36000" weight="300" foreground="#2c3e50">')
                    elif self.style == "modest":
                        self.output.append('\n<span size="28000" weight="bold" foreground="#333">')
                    elif self.style == "retro":
                        self.output.append('\n<span size="30000" weight="bold" foreground="#8b4513">')
                    elif self.style == "air":
                        self.output.append('\n<span size="32000" weight="300" foreground="#2aa198">')
                    else:
                        self.output.append('\n<span size="24000" weight="bold">')
                elif tag == 'h2':
                    self.in_heading_level = 2
                    if self.style == "github":
                        self.output.append('\n<span size="24000" weight="bold" foreground="#1f2328">')
                    elif self.style == "github-light":
                        self.output.append('\n<span size="26000" weight="600" foreground="#1f2328">')
                    elif self.style == "github-dark":
                        self.output.append('\n<span size="26000" weight="600" foreground="#f0f6fc">')
                    elif self.style == "gitlab":
                        self.output.append('\n<span size="24000" weight="bold" foreground="#303030">')
                    elif self.style == "splendor":
                        self.output.append('\n<span size="28000" weight="400" foreground="#34495e">')
                    elif self.style == "modest":
                        self.output.append('\n<span size="24000" weight="bold" foreground="#444">')
                    elif self.style == "retro":
                        self.output.append('\n<span size="26000" weight="bold" foreground="#a0522d">')
                    elif self.style == "air":
                        self.output.append('\n<span size="26000" weight="400" foreground="#268bd2">')
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
                    if self.style == "github" or self.style == "github-light":
                        self.output.append('<span weight="bold" foreground="#1f2328">')
                    elif self.style == "github-dark":
                        self.output.append('<span weight="600" foreground="#f0f6fc">')
                    elif self.style == "gitlab":
                        self.output.append('<span weight="bold" foreground="#303030">')
                    elif self.style == "splendor":
                        self.output.append('<span weight="600" foreground="#2c3e50">')
                    elif self.style == "modest":
                        self.output.append('<span weight="bold" foreground="#333">')
                    elif self.style == "retro":
                        self.output.append('<span weight="bold" foreground="#8b4513">')
                    elif self.style == "air":
                        self.output.append('<span weight="600" foreground="#2aa198">')
                    else:
                        self.output.append('<b>')
                elif tag == 'em' or tag == 'i':
                    if self.style == "github" or self.style == "github-light":
                        self.output.append('<span style="italic" foreground="#656d76">')
                    elif self.style == "github-dark":
                        self.output.append('<span style="italic" foreground="#8b949e">')
                    elif self.style == "gitlab":
                        self.output.append('<span style="italic" foreground="#525252">')
                    elif self.style == "splendor":
                        self.output.append('<span style="italic" foreground="#7f8c8d">')
                    elif self.style == "modest":
                        self.output.append('<span style="italic" foreground="#666">')
                    elif self.style == "retro":
                        self.output.append('<span style="italic" foreground="#8b7355">')
                    elif self.style == "air":
                        self.output.append('<span style="italic" foreground="#586e75">')
                    else:
                        self.output.append('<i>')
                elif tag == 'u':
                    self.output.append('<u>')
                elif tag == 'code':
                    if not self.in_code_block:
                        if self.style == "github":
                            self.output.append('<span font_family="monospace" background="#f6f8fa" foreground="#d1242f" size="small"> ')
                        elif self.style == "github-light":
                            self.output.append('<span font_family="monospace" background="#afb8c133" foreground="#d1242f" size="small"> ')
                        elif self.style == "github-dark":
                            self.output.append('<span font_family="monospace" background="#6e768166" foreground="#ff7b72" size="small"> ')
                        elif self.style == "gitlab":
                            self.output.append('<span font_family="monospace" background="#fdf2f2" foreground="#c73e1d" size="small"> ')
                        elif self.style == "splendor":
                            self.output.append('<span font_family="monospace" background="#ecf0f1" foreground="#e74c3c" size="small"> ')
                        elif self.style == "modest":
                            self.output.append('<span font_family="monospace" background="#f5f5f5" foreground="#d14" size="small"> ')
                        elif self.style == "retro":
                            self.output.append('<span font_family="monospace" background="#eee8d5" foreground="#b58900" size="small"> ')
                        elif self.style == "air":
                            self.output.append('<span font_family="monospace" background="#eee8d5" foreground="#cb4b16" size="small"> ')
                        else:
                            self.output.append('<span font_family="monospace" background="#e0e0e0">')
                elif tag == 'pre':
                    self.in_code_block = True
                    if self.style == "github":
                        self.output.append('\n<span font_family="monospace" background="#f6f8fa" foreground="#24292f">')
                    elif self.style == "github-light":
                        self.output.append('\n<span font_family="monospace" background="#f6f8fa" foreground="#24292f">')
                    elif self.style == "github-dark":
                        self.output.append('\n<span font_family="monospace" background="#161b22" foreground="#e6edf3">')
                    elif self.style == "gitlab":
                        self.output.append('\n<span font_family="monospace" background="#fbfafd" foreground="#303030">')
                    elif self.style == "splendor":
                        self.output.append('\n<span font_family="monospace" background="#fafafa" foreground="#333">')
                    elif self.style == "modest":
                        self.output.append('\n<span font_family="monospace" background="#f5f5f5" foreground="#333">')
                    elif self.style == "retro":
                        self.output.append('\n<span font_family="monospace" background="#eee8d5" foreground="#657b83">')
                    elif self.style == "air":
                        self.output.append('\n<span font_family="monospace" background="#fafafa" foreground="#586e75">')
                    else:
                        self.output.append('\n<span font_family="monospace" background="#e3e3e3">')
                elif tag == 'p':
                    if self.output and not self.output[-1].endswith('\n'):
                        self.output.append('\n')
                elif tag == 'br':
                    self.output.append('\n')
                elif tag == 'hr':
                    if self.style == "github" or self.style == "github-light":
                        self.output.append('\n<span foreground="#d1d9e0">' + '─' * 50 + '</span>\n')
                    elif self.style == "github-dark":
                        self.output.append('\n<span foreground="#30363d">' + '─' * 60 + '</span>\n')
                    elif self.style == "gitlab":
                        self.output.append('\n<span foreground="#6b4fbb">' + '─' * 60 + '</span>\n')
                    elif self.style == "splendor":
                        self.output.append('\n<span foreground="#bdc3c7">' + '╌' * 50 + '</span>\n')
                    elif self.style == "retro":
                        self.output.append('\n<span foreground="#cd853f">' + '╌' * 50 + '</span>\n')
                    else:
                        self.output.append('\n' + '─' * 50 + '\n')
                elif tag == 'blockquote':
                    if self.style == "github" or self.style == "github-light":
                        self.output.append('\n<span style="italic" foreground="#656d76" background="#f6f8fa">▎ ')
                    elif self.style == "github-dark":
                        self.output.append('\n<span style="italic" foreground="#8b949e" background="#161b22">▎ ')
                    elif self.style == "gitlab":
                        self.output.append('\n<span style="italic" foreground="#6b4fbb" background="#fbfafd">▎ ')
                    elif self.style == "splendor":
                        self.output.append('\n<span style="italic" foreground="#7f8c8d" background="#ecf0f1">" ')
                    elif self.style == "modest":
                        self.output.append('\n<span style="italic" foreground="#777" background="#f9f9f9">│ ')
                    elif self.style == "retro":
                        self.output.append('\n<span style="italic" foreground="#8b7355" background="#f5f5dc">▌ ')
                    elif self.style == "air":
                        self.output.append('\n<span style="italic" foreground="#93a1a1" background="#fdf6e3">  ')
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
                    parent = self.tag_stack[-2] if len(self.tag_stack) > 1 else None
                    btype = 'ul'
                    if parent == 'ol': btype = 'ol'
                    self.pending_li_content = (indent, btype)
                elif tag == 'del' or tag == 's':
                    self.output.append('<s>')
                elif tag == 'a':
                    if self.style == "github" or self.style == "github-light":
                        self.output.append('<span foreground="#0969da" underline="single">')
                    elif self.style == "github-dark":
                        self.output.append('<span foreground="#58a6ff" underline="single">')
                    elif self.style == "gitlab":
                        self.output.append('<span foreground="#1f75cb" underline="single" weight="medium">')
                    elif self.style == "splendor":
                        self.output.append('<span foreground="#3498db" underline="single">')
                    elif self.style == "modest":
                        self.output.append('<span foreground="#337ab7" underline="single">')
                    elif self.style == "retro":
                        self.output.append('<span foreground="#268bd2" underline="single">')
                    elif self.style == "air":
                        self.output.append('<span foreground="#268bd2" underline="single">')
                    else:
                        self.output.append('<span foreground="blue" underline="single">')
                elif tag == 'img':
                    alt = next((value for name, value in attrs if name == 'alt'), _('Image'))
                    self.output.append(f'\n🖼️ [{_("Image")}: {alt}]\n')
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
                self.flush_pending_li()
                
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
                    if self.style == "default":
                        self.output.append('</b>')
                    else:
                        self.output.append('</span>')
                elif tag == 'em' or tag == 'i':
                    if self.style == "default":
                        self.output.append('</i>')
                    else:
                        self.output.append('</span>')
                elif tag == 'u':
                    self.output.append('</u>')
                elif tag == 'del' or tag == 's':
                    self.output.append('</s>')
                elif tag == 'code':
                    if not self.in_code_block:
                        self.output.append(' </span>')
                    else:
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
                if self.pending_li_content:
                    match = re.match(r'^(\s*)\[([ xX])\]\s+(.*)', data)
                    if not match:
                        match = re.match(r'^(\s*)\[([ xX])\]$', data)
                        
                    if match:
                        indent, _ = self.pending_li_content
                        is_checked = match.group(2).lower() == 'x'
                        
                        checkbox = "☑ " if is_checked else "☐ "
                        
                        if self.style == "github" or self.style == "github-light":
                            checkbox = f'<span foreground="#1f2328">{checkbox}</span>'
                        elif self.style == "github-dark":
                            checkbox = f'<span foreground="#f0f6fc">{checkbox}</span>'
                        elif self.style == "gitlab":
                            checkbox = f'<span foreground="#303030">{checkbox}</span>'
                        elif self.style == "splendor":
                            checkbox = f'<span foreground="#2c3e50">{checkbox}</span>'
                        elif self.style == "modest":
                            checkbox = f'<span foreground="#333">{checkbox}</span>'
                        elif self.style == "retro":
                            checkbox = f'<span foreground="#8b4513">{checkbox}</span>'
                        elif self.style == "air":
                            checkbox = f'<span foreground="#268bd2">{checkbox}</span>'
                            
                        self.output.append(f'{indent}{checkbox}')
                        
                        data = data[match.end():]
                        if match.lastindex >= 3:
                            data = match.group(3) or ""
                            
                        # First escape data before wrapping in tags
                        data = data.replace('&', '&amp;')
                        data = data.replace('<', '&lt;')
                        data = data.replace('>', '&gt;')
                        
                        if is_checked:
                            data = f"<s>{data}</s>"
                            
                        self.output.append(data)
                        self.pending_li_content = None
                        return
                    else:
                        self.flush_pending_li()
                
                # First escape XML characters
                data = data.replace('&', '&amp;')
                data = data.replace('<', '&lt;')
                data = data.replace('>', '&gt;')
                
                # Then process strikethrough (after escaping)
                data = re.sub(r'~~([^~]+?)~~', r'<s>\1</s>', data)
                
                self.output.append(data)
                
            def get_pango(self):
                self.flush_pending_li()
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
                result.append(f'<span size="24000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format(stripped_line[3:])
                result.append(f'<span size="20000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format(stripped_line[4:])
                result.append(f'<span size="18000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format(stripped_line[5:])
                result.append(f'<span size="16000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format(stripped_line[6:])
                result.append(f'<span size="14000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format(stripped_line[7:])
                result.append(f'<span size="12000" weight="bold">{processed}</span>')
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
                result.append(f'<span style="italic" foreground="#666666">" {processed} "</span>')
            elif stripped_line.strip() == '---':
                result.append('─' * 50)
            else:
                if stripped_line:
                    processed = self._process_inline_format(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format(self, text):
        if not text:
            return text
            
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<b>\1</b>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="monospace" background="#e0e0e0">\1</span>', processed)
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="blue" underline="single">\1</span>', processed)
        
        return processed

class GitHubRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "github"

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
                    result.append('<span font_family="SFMono-Regular,Consolas" background="#f6f8fa" foreground="#24292f">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_github(stripped_line[2:])
                result.append(f'<span size="28000" weight="bold" foreground="#1f2328">{processed}</span>')
                result.append('<span foreground="#d1d9e0">' + '─' * 60 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_github(stripped_line[3:])
                result.append(f'<span size="24000" weight="bold" foreground="#1f2328">{processed}</span>')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_github(stripped_line[2:])
                result.append(f'<span style="italic" foreground="#656d76" background="#f6f8fa">▎ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_github(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_github(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="bold" foreground="#1f2328">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#656d76">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="SFMono-Regular" background="#f6f8fa" foreground="#d1242f" size="small"> \1 </span>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#0969da" underline="single">\1</span>', processed)
        return processed

class GitHubLightRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "github-light"

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
                    result.append('<span font_family="SFMono-Regular,Consolas" background="#f6f8fa" foreground="#24292f">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_github_light(stripped_line[2:])
                result.append(f'<span size="32000" weight="600" foreground="#1f2328">{processed}</span>')
                result.append('<span foreground="#d1d9e0">' + '─' * 60 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_github_light(stripped_line[3:])
                result.append(f'<span size="26000" weight="600" foreground="#1f2328">{processed}</span>')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_github_light(stripped_line[2:])
                result.append(f'<span style="italic" foreground="#636c76" background="#f6f8fa">▎ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_github_light(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_github_light(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="600" foreground="#1f2328">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#636c76">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="SFMono-Regular" background="#afb8c133" foreground="#d1242f" size="small"> \1 </span>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#0969da" underline="single">\1</span>', processed)
        return processed

class GitHubDarkRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "github-dark"

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
                    result.append('<span font_family="SFMono-Regular,Consolas" background="#161b22" foreground="#e6edf3">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_github_dark(stripped_line[2:])
                result.append(f'<span size="32000" weight="600" foreground="#f0f6fc">{processed}</span>')
                result.append('<span foreground="#30363d">' + '─' * 60 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_github_dark(stripped_line[3:])
                result.append(f'<span size="26000" weight="600" foreground="#f0f6fc">{processed}</span>')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_github_dark(stripped_line[2:])
                result.append(f'<span style="italic" foreground="#8b949e" background="#161b22">▎ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_github_dark(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_github_dark(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="600" foreground="#f0f6fc">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#8b949e">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="SFMono-Regular" background="#6e768166" foreground="#ff7b72" size="small"> \1 </span>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#58a6ff" underline="single">\1</span>', processed)
        return processed

class GitLabRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "gitlab"

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
                    result.append('<span font_family="JetBrains Mono,Consolas" background="#fbfafd" foreground="#303030">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_gitlab(stripped_line[2:])
                result.append(f'<span size="28000" weight="bold" foreground="#303030">{processed}</span>')
                result.append('<span foreground="#6b4fbb">' + '─' * 60 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_gitlab(stripped_line[3:])
                result.append(f'<span size="24000" weight="bold" foreground="#303030">{processed}</span>')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_gitlab(stripped_line[2:])
                result.append(f'<span style="italic" foreground="#6b4fbb" background="#fbfafd">▎ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_gitlab(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_gitlab(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="bold" foreground="#303030">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#525252">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="JetBrains Mono" background="#fdf2f2" foreground="#c73e1d" size="small"> \1 </span>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#1f75cb" underline="single" weight="medium">\1</span>', processed)
        return processed

class SplendorRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "splendor"

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
                    result.append('<span font_family="Consolas,Monaco" background="#fafafa" foreground="#333">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_splendor(stripped_line[2:])
                result.append(f'<span size="36000" weight="300" foreground="#2c3e50">{processed}</span>')
                result.append('<span foreground="#bdc3c7">' + '╌' * 50 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_splendor(stripped_line[3:])
                result.append(f'<span size="28000" weight="400" foreground="#34495e">{processed}</span>')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_splendor(stripped_line[2:])
                result.append(f'<span style="italic" foreground="#7f8c8d" background="#ecf0f1">" {processed} "</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_splendor(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_splendor(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="600" foreground="#2c3e50">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#7f8c8d">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="Consolas" background="#ecf0f1" foreground="#e74c3c" size="small"> \1 </span>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#3498db" underline="single">\1</span>', processed)
        return processed

class ModestRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "modest"

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
                    result.append('<span font_family="Menlo,Monaco" background="#f5f5f5" foreground="#333">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_modest(stripped_line[2:])
                result.append(f'<span size="28000" weight="bold" foreground="#333">{processed}</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_modest(stripped_line[3:])
                result.append(f'<span size="24000" weight="bold" foreground="#444">{processed}</span>')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_modest(stripped_line[2:])
                result.append(f'<span style="italic" foreground="#777" background="#f9f9f9">│ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_modest(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_modest(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="bold" foreground="#333">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#666">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="Menlo" background="#f5f5f5" foreground="#d14" size="small"> \1 </span>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#337ab7" underline="single">\1</span>', processed)
        return processed

class RetroRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "retro"

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
                    result.append('<span font_family="Courier New,monospace" background="#eee8d5" foreground="#657b83">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_retro(stripped_line[2:])
                result.append(f'<span size="30000" weight="bold" foreground="#8b4513">{processed}</span>')
                result.append('<span foreground="#cd853f">' + '╌' * 50 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_retro(stripped_line[3:])
                result.append(f'<span size="26000" weight="bold" foreground="#a0522d">{processed}</span>')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_retro(stripped_line[2:])
                result.append(f'<span style="italic" foreground="#8b7355" background="#f5f5dc">▌ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_retro(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_retro(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="bold" foreground="#8b4513">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#8b7355">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="Courier New" background="#eee8d5" foreground="#b58900" size="small"> \1 </span>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#268bd2" underline="single">\1</span>', processed)
        return processed

class AirRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "air"

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
                    result.append('<span font_family="Source Code Pro,monospace" background="#fafafa" foreground="#586e75">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_air(stripped_line[2:])
                result.append(f'<span size="32000" weight="300" foreground="#2aa198">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_air(stripped_line[3:])
                result.append(f'<span size="26000" weight="400" foreground="#268bd2">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_air(stripped_line[2:])
                result.append(f'<span style="italic" foreground="#93a1a1" background="#fdf6e3">  {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_air(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_air(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="600" foreground="#2aa198">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#586e75">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="Source Code Pro" background="#eee8d5" foreground="#cb4b16" size="small"> \1 </span>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<span foreground="#268bd2" underline="single">\1</span>', processed)
        return processed

class ScrollSyncMixin:
    def setup_scroll_sync(self):
        if not hasattr(self, 'editor_scroll') or not hasattr(self, 'preview_scroll'):
            return
            
        self.sync_scroll_enabled = True
        self.click_in_progress = False
        
        self.editor_vadj = self.editor_scroll.get_vadjustment()
        self.preview_vadj = self.preview_scroll.get_vadjustment()
        
        self.editor_vadj.connect("value-changed", self.on_editor_scroll)
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
    
    def disable_scroll_sync(self):
        self.sync_scroll_enabled = False
    
    def enable_scroll_sync(self):
        self.sync_scroll_enabled = True

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
            self.search_entry.grab_focus()
            self.search_entry.select_region(0, -1)
    
    def hide_search(self):
        if hasattr(self, 'search_bar'):
            self.search_bar.set_search_mode(False)
        self.clear_search_highlights()
        if hasattr(self, 'text_view'):
            self.text_view.grab_focus()
    
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

class FileOperationsMixin:
    def on_open(self, widget):
        if not Gtk:
            return
            
        dialog = Gtk.FileChooserNative.new(
            _("Open file"),
            self,
            Gtk.FileChooserAction.OPEN,
            _("_Open"),
            _("_Cancel")
        )

        filter_md = Gtk.FileFilter()
        filter_md.set_name(_("Markdown files"))
        filter_md.add_mime_type("text/markdown")
        filter_md.add_pattern("*.md")
        filter_md.add_pattern("*.markdown")
        filter_md.add_pattern("*.mdown")
        filter_md.add_pattern("*.mkd")
        dialog.add_filter(filter_md)

        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("All files"))
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        dialog.connect("response", self.on_open_dialog_response)
        dialog.show()

    def on_open_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                self.load_file(file.get_path())
        dialog.destroy()
    
    def on_save(self, widget):
        if self.current_file:
            self.save_file()
        else:
            self.save_as()
    
    def save_as(self):
        if not Gtk:
            return
            
        dialog = Gtk.FileChooserNative.new(
            _("Save file"),
            self,
            Gtk.FileChooserAction.SAVE,
            _("_Save"),
            _("_Cancel")
        )
        dialog.set_current_name(_("untitled.md"))

        filter_md = Gtk.FileFilter()
        filter_md.set_name(_("Markdown files"))
        filter_md.add_mime_type("text/markdown")
        filter_md.add_pattern("*.md")
        dialog.add_filter(filter_md)

        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("All files"))
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        dialog.connect("response", self.on_save_dialog_response)
        dialog.show()

    def on_save_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                self.current_file = file.get_path()
                self.save_file()
                self.update_title()
                self.update_header()
        dialog.destroy()
    
    def load_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if hasattr(self, 'text_buffer'):
                self.text_buffer.set_text(content)
                
            self.current_file = file_path
            self.document_modified = False
            
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
            return
            
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
            
            if hasattr(self, 'doc_status_label'):
                self.doc_status_label.set_text(_("Saved"))
            
        except Exception as e:
            print(f"Error saving file: {e}")
            self.show_error_dialog(f"{_('Error')}: {str(e)}")
    
    def show_error_dialog(self, message):
        if not Adw:
            print(f"Error: {message}")
            return
            
        dialog = Adw.MessageDialog.new(self, _("Error"), message)
        dialog.add_response("ok", _("Accept"))
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
    
    def update_title(self):
        if self.current_file:
            filename = os.path.basename(self.current_file)
            self.set_title(f"{filename} - {_('Markdown Editor')}")
        else:
            self.set_title(f"{_('New document')} - {_('Markdown Editor')}")

    def update_header(self):
        pass
    
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
    
    def on_new(self, button):
        try:
            if (hasattr(self, 'content_stack') and 
                self.content_stack.get_visible_child_name() == "welcome"):
                self.on_new_from_welcome(None)
            else:
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
        except Exception as e:
            print(f"Error creating new document: {e}")

class EditorActionsMixin:
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
            
        try:
            table_text = f"""| {_('Header 1')} | {_('Header 2')} | {_('Header 3')} |
|--------------|--------------|--------------|
| {_('Cell 1')}      | {_('Cell 2')}      | {_('Cell 3')}      |
| {_('Cell 4')}      | {_('Cell 5')}      | {_('Cell 6')}      |
"""
            self.text_buffer.insert_at_cursor(table_text)
        except Exception as e:
            print(f"Error inserting table: {e}")

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
            
            list_patterns = [
                (r'^(\s*)-\s+(.*)$', r'\1- '),
                (r'^(\s*)\*\s+(.*)$', r'\1* '),
                (r'^(\s*)\+\s+(.*)$', r'\1+ '),
                (r'^(\s*)(\d+)\.\s+(.*)$', r'\1{}. '),
                (r'^(\s*)-\s+\[\s*\]\s+(.*)$', r'\1- [ ] '),
                (r'^(\s*)-\s+\[x\]\s+(.*)$', r'\1- [ ] '),
            ]
            
            for pattern, replacement in list_patterns:
                match = re.match(pattern, current_line)
                if match:
                    if len(match.groups()) >= 2 and not match.group(-1).strip():
                        self.text_buffer.delete(line_start, iter_at_cursor)
                        self.in_list_context = False
                        return False
                    
                    if '{}' in replacement:
                        try:
                            next_num = int(match.group(2)) + 1
                            new_prefix = replacement.format(next_num)
                        except (ValueError, IndexError):
                            new_prefix = replacement.replace('{}', '1')
                    else:
                        new_prefix = replacement
                    
                    self.text_buffer.insert_at_cursor(f"\n{new_prefix}")
                    return True
            
            self.in_list_context = False
            return False

            
        except Exception as e:
            print(f"Error handling Enter: {e}")
            return False            
    
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
            lines = text.split('\n')
            words = len([word for word in text.split() if word.strip()])
            size_bytes = len(text.encode('utf-8'))
            
            if hasattr(self, 'lines_label'):
                self.lines_label.set_text(f"{len(lines)} {_('lines')}")
            if hasattr(self, 'words_label'):
                self.words_label.set_text(f"{words} {_('words')}")
            
            if size_bytes < 1024:
                size_text = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_text = f"{size_bytes / 1024:.1f} KB"
            else:
                size_text = f"{size_bytes / (1024 * 1024):.1f} MB"
            
            if hasattr(self, 'size_label'):
                self.size_label.set_text(size_text)
                
            self.update_cursor_position()
            
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
            
            if hasattr(self, 'renderer') and hasattr(self, 'preview_label'):
                preview_text = self.renderer.render_text(text)
                
                try:
                    self.preview_label.set_text("")
                    self.preview_label.set_markup(preview_text)
                except Exception as e:
                    print(f"Error in set_markup: {e}")
                    self.preview_label.set_text(text)
            
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

class MarkdownEditorWindow(Adw.ApplicationWindow, ScrollSyncMixin, SearchMixin, 
                          FileOperationsMixin, EditorActionsMixin):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            
            self.config = Config()
            self.current_file = None
            self.document_modified = False
            self.current_language = self.config.get("language", "auto")
            
            self.click_in_progress = False
            
            self.apply_render_style()
            
            self.set_title(_("Markdown Editor"))
            self.set_default_size(1000, 700)
            
            self.apply_saved_config()
            self.setup_ui()
            self.setup_shortcuts()
            self.connect("close-request", self.on_close)
            
        except Exception as e:
            print(f"Error initializing window: {e}")
            raise
    
    def apply_saved_config(self):
        saved_language = self.config.get("language", "auto")
        if saved_language != "auto":
            global _
            _ = setup_locale(saved_language)
            self.current_language = saved_language

        dark_theme = self.config.get("dark_theme", False)
        self.apply_theme(dark_theme)

    def change_language(self, language_code):
        global _
        _ = setup_locale(language_code if language_code != "auto" else None)
        self.config.set("language", language_code)
        self.current_language = language_code

        self.recreate_ui()

    def recreate_ui(self):
        """Recreate UI elements to apply new language"""
        if self.current_file:
            filename = os.path.basename(self.current_file)
            self.set_title(f"{filename} - {_('Markdown Editor')}")
        else:
            self.set_title(_("Markdown Editor"))
        
        # Update header bar title
        if hasattr(self, 'get_titlebar'):
            header_bar = self.get_titlebar()
            if header_bar and hasattr(header_bar, 'get_title_widget'):
                title_widget = header_bar.get_title_widget()
                if title_widget:
                    title_widget.set_label(_("Markdown Editor"))
        
        # Update tooltips and labels
        if hasattr(self, 'new_btn'):
            self.new_btn.set_tooltip_text(_("New document"))
        if hasattr(self, 'open_btn'):
            self.open_btn.set_tooltip_text(_("Open file"))
        if hasattr(self, 'save_btn'):
            self.save_btn.set_tooltip_text(_("Save file"))
        if hasattr(self, 'search_btn'):
            self.search_btn.set_tooltip_text(_("Search (Ctrl+F)"))
        
        # Update search bar placeholder if visible
        if hasattr(self, 'search_entry'):
            self.search_entry.set_placeholder_text(_("Search in document..."))
        
        # Update status labels
        if hasattr(self, 'doc_status_label'):
            current_status = self.doc_status_label.get_text()
            if "Modified" in current_status or "Modificado" in current_status:
                self.doc_status_label.set_text(_("Modified"))
            elif "Saved" in current_status or "Guardado" in current_status:
                self.doc_status_label.set_text(_("Saved"))
            elif "Ready" in current_status or "Listo" in current_status:
                self.doc_status_label.set_text(_("Ready"))
        
        # Update status bar labels - NUEVA SECCIÓN
        if hasattr(self, 'text_buffer'):
            # Trigger a refresh of the statistics with current language
            text = self.text_buffer.get_text(
                self.text_buffer.get_start_iter(),
                self.text_buffer.get_end_iter(),
                False
            )
            self.update_detailed_stats(text)
        else:
            # Update labels even without content
            if hasattr(self, 'lines_label'):
                self.lines_label.set_text(f"1 {_('lines')}")
            if hasattr(self, 'words_label'):
                self.words_label.set_text(f"0 {_('words')}")
            if hasattr(self, 'cursor_label'):
                self.cursor_label.set_text(f"{_('Line')} 1, {_('Col')} 1")
        
        # Update welcome page if visible
        if (hasattr(self, 'content_stack') and 
            self.content_stack.get_visible_child_name() == "welcome"):
            self.update_welcome_page_language()

    def update_welcome_page_language(self):
        """Update welcome page texts with current language"""
        if hasattr(self, 'welcome_title'):
            self.welcome_title.set_markup(
                f"<span size='x-large' weight='bold'>{_('Markdown Editor')}</span>"
            )
        if hasattr(self, 'welcome_subtitle'):
            self.welcome_subtitle.set_text(
                _("Create and edit Markdown documents with real-time preview")
            )
        if hasattr(self, 'welcome_info'):
            self.welcome_info.set_text(
                _("You can also use Ctrl+N to create a new file or Ctrl+O to open an existing one")
            )
        
        # También actualizar los textos de las tarjetas de bienvenida
        if hasattr(self, 'welcome_page'):
            self.recreate_welcome_cards()

    def recreate_welcome_cards(self):
        """Recreate welcome cards with updated language"""
        # Buscar el contenedor de opciones y recrearlo
        welcome_container = self.welcome_page
        # Encontrar el options_box (tercer elemento después del ícono, título y subtítulo)
        children = []
        child = welcome_container.get_first_child()
        while child:
            children.append(child)
            child = child.get_next_sibling()
        
        if len(children) >= 4:  # ícono, título, subtítulo, options_box
            options_box = children[3]
            welcome_container.remove(options_box)
            
            # Crear nuevo options_box con textos actualizados
            new_options_box = self.create_welcome_options()
            welcome_container.insert_child_after(new_options_box, children[2])            

    def apply_theme(self, dark_theme):
        if not Adw:
            return
        style_manager = Adw.StyleManager.get_default()
        if dark_theme:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)

    def setup_ui(self):
        if not Gtk:
            return
            
        try:
            header_bar = Gtk.HeaderBar()
            header_bar.set_title_widget(Gtk.Label(label=_("Markdown Editor")))
            
            self.new_btn = Gtk.Button()
            self.new_btn.set_icon_name("document-new-symbolic")
            self.new_btn.set_tooltip_text(_("New document"))
            self.new_btn.connect("clicked", self.on_new)
            header_bar.pack_start(self.new_btn)
            
            self.open_btn = Gtk.Button()
            self.open_btn.set_icon_name("document-open-symbolic")
            self.open_btn.set_tooltip_text(_("Open file"))
            self.open_btn.connect("clicked", self.on_open)
            header_bar.pack_start(self.open_btn)
            
            self.save_btn = Gtk.Button()
            self.save_btn.set_icon_name("document-save-symbolic")
            self.save_btn.set_tooltip_text(_("Save file"))
            self.save_btn.connect("clicked", self.on_save)
            self.save_btn.set_sensitive(False)
            header_bar.pack_start(self.save_btn)
        
            
            self.search_btn = Gtk.Button()
            self.search_btn.set_icon_name("system-search-symbolic")
            self.search_btn.set_tooltip_text(_("Search (Ctrl+F)"))
            self.search_btn.connect("clicked", lambda x: self.toggle_search())
            header_bar.pack_start(self.search_btn)
            
            self.setup_menu_button(header_bar)
            
            # Create a vertical box for the main content
            main_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            main_content_box.append(header_bar)
            
            self.set_content(main_content_box)
            
            self.setup_main_layout(main_content_box)
            
            self.apply_css()
            
            self.show_welcome_state()
            
        except Exception as e:
            print(f"Error setting up UI: {e}")
            raise

    def setup_menu_button(self, header_bar):
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text(_("Application menu"))
        
        menu_model = Gio.Menu()
        
        main_section = Gio.Menu()
        main_section.append(_("Print..."), "app.print")
        menu_model.append_section(None, main_section)
        
        language_menu = Gio.Menu()
        language_menu.append(_("Auto-detect"), "app.language::auto")
        language_menu.append(_("English"), "app.language::en")
        language_menu.append(_("Spanish"), "app.language::es")
        menu_model.append_submenu(_("Language"), language_menu)
        
        menu_model.append(_("Preferences"), "app.preferences")
        menu_model.append(_("About"), "app.about")
        
        menu_button.set_menu_model(menu_model)
        header_bar.pack_end(menu_button)

    def setup_main_layout(self, parent_box):
        overlay = Gtk.Overlay()
        
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        
        self.welcome_page = self.create_welcome_page()
        self.content_stack.add_named(self.welcome_page, "welcome")
        
        self.editor_area = self.create_editor_area()
        self.content_stack.add_named(self.editor_area, "editor")
        
        overlay.set_child(self.content_stack)
        
        # Make the overlay expand to fill available space
        overlay.set_hexpand(True)
        overlay.set_vexpand(True)
        
        parent_box.append(overlay)

    def create_welcome_page(self):
        welcome_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        welcome_container.set_valign(Gtk.Align.CENTER)
        welcome_container.set_halign(Gtk.Align.CENTER)
        welcome_container.set_spacing(40)
        welcome_container.set_margin_start(40)
        welcome_container.set_margin_end(40)
        
        icon = Gtk.Image()
        icon.set_from_icon_name("text-markdown-symbolic")
        icon.set_pixel_size(128)
        icon.add_css_class("dim-label")
        icon.set_margin_top(50) 
        welcome_container.append(icon)
        
        self.welcome_title = Gtk.Label()
        self.welcome_title.set_markup(
            f"<span size='x-large' weight='bold'>{_('Markdown Editor')}</span>"
        )
        self.welcome_title.add_css_class("title-1")
        welcome_container.append(self.welcome_title)
        
        self.welcome_subtitle = Gtk.Label()
        self.welcome_subtitle.set_text(_("Create and edit Markdown documents with real-time preview"))
        self.welcome_subtitle.add_css_class("dim-label")
        self.welcome_subtitle.set_wrap(True)
        self.welcome_subtitle.set_justify(Gtk.Justification.CENTER)
        welcome_container.append(self.welcome_subtitle)
        
        options_box = self.create_welcome_options()
        welcome_container.append(options_box)
        
        self.welcome_info = Gtk.Label()
        self.welcome_info.set_text(_("You can also use Ctrl+N to create a new file or Ctrl+O to open an existing one"))
        self.welcome_info.add_css_class("dim-label")
        self.welcome_info.set_margin_top(40)
        self.welcome_info.set_wrap(True)
        self.welcome_info.set_justify(Gtk.Justification.CENTER)
        welcome_container.append(self.welcome_info)

        return welcome_container

    def create_welcome_options(self):
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        options_box.set_spacing(30)
        options_box.set_halign(Gtk.Align.CENTER)
        
        new_file_card = self.create_welcome_card(
            "document-new-symbolic",
            _("New Document"),
            _("Create a new blank Markdown document"),
            _("Create New"),
            self.on_new_from_welcome
        )
        options_box.append(new_file_card)
        
        open_file_card = self.create_welcome_card(
            "document-open-symbolic",
            _("Open File"), 
            _("Open an existing Markdown document"),
            _("Open File"),
            self.on_open_from_welcome
        )
        options_box.append(open_file_card)
        
        return options_box

    def create_welcome_card(self, icon_name, title, description, button_text, callback):
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
        
        desc = Gtk.Label()
        desc.set_text(description)
        desc.add_css_class("dim-label")
        desc.set_wrap(True)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_margin_top(10)
        card.append(desc)
        
        button = Gtk.Button()
        button.set_label(button_text)
        button.add_css_class("suggested-action")
        button.add_css_class("pill")
        button.set_margin_top(20)
        button.connect("clicked", callback)
        card.append(button)
        
        return card

    def create_editor_area(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        toolbar_container = self.create_toolbar()
        main_box.append(toolbar_container)
        
        self.create_main_panels(main_box)
        
        self.search_bar = self.create_search_bar()
        main_box.append(self.search_bar)
        
        status_bar = self.create_status_bar()
        main_box.append(status_bar)
        
        return main_box

    def create_toolbar(self):
        toolbar_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        toolbar_container.add_css_class("toolbar")
        toolbar_container.set_margin_start(8)
        toolbar_container.set_margin_end(8)
        toolbar_container.set_margin_top(4)
        toolbar_container.set_margin_bottom(4)
        
        toolbar = self.create_format_buttons()
        toolbar_container.append(toolbar)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar_container.append(spacer)
        
        view_buttons = self.create_view_buttons()
        toolbar_container.append(view_buttons)
        
        return toolbar_container

    def create_format_buttons(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        toolbar.set_spacing(0)
        toolbar.set_halign(Gtk.Align.START)
        
        def create_icon_button(icon_name, tooltip, callback=None):
            btn = Gtk.Button()
            btn.set_icon_name(icon_name)
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
        
        toolbar.append(create_icon_button("format-text-bold-symbolic", _("Bold (Ctrl+B)"), 
                                        lambda x: self.insert_format("**", "**")))
        toolbar.append(create_icon_button("format-text-italic-symbolic", _("Italic (Ctrl+I)"), 
                                        lambda x: self.insert_format("*", "*")))
        toolbar.append(create_icon_button("format-text-strikethrough-symbolic", _("Strikethrough"), 
                                        lambda x: self.insert_format("~~", "~~")))
        
        headers_button = self.create_headers_menu()
        toolbar.append(headers_button)
        
        add_separator()
        
        toolbar.append(create_icon_button("view-list-bullet-symbolic", _("Bullet list"), 
                                        lambda x: self.insert_list_item("unordered")))
        toolbar.append(create_icon_button("format-ordered-list-symbolic", _("Numbered list"), 
                                        lambda x: self.insert_list_item("ordered")))
        toolbar.append(create_icon_button("view-list-details-symbolic", _("Task list"), 
                                        lambda x: self.insert_list_item("task")))
        toolbar.append(create_icon_button("format-text-blockquote-symbolic", _("Quote"), 
                                        lambda x: self.insert_format("> ", "")))
        
        add_separator()
        
        toolbar.append(create_icon_button("format-text-code-symbolic", _("Inline code"), 
                                        lambda x: self.insert_format("`", "`")))
        toolbar.append(create_icon_button("code-context-symbolic", _("Code block"), 
                                        lambda x: self.insert_format("```\n", "\n```")))
        
        add_separator()
        
        toolbar.append(create_icon_button("insert-link-symbolic", _("Insert link (Ctrl+K)"), 
                                        lambda x: self.insert_format("[", "](https://pabmartine.com)")))
        toolbar.append(create_icon_button("folder-images-symbolic", _("Insert image"), 
                                        lambda x: self.insert_format("![", "](image.png)")))
        toolbar.append(create_icon_button("folder-table-symbolic", _("Insert table"), self.insert_table))
        
        add_separator()
        
        toolbar.append(create_icon_button("menu_new_sep-symbolic", _("Horizontal line"), 
                                        lambda x: self.insert_format("\n---\n", "")))
        
        return toolbar

    def create_headers_menu(self):
        headers_button = Gtk.MenuButton()
        headers_button.set_icon_name("format-text-larger-symbolic")
        headers_button.set_tooltip_text(_("Select header"))
        headers_button.add_css_class("super-compact-btn")
        headers_button.set_size_request(18, 18)
        
        popover = Gtk.Popover()
        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        popover_box.set_spacing(0)
        
        header_data = [("H1", "# "), ("H2", "## "), ("H3", "### "), 
                      ("H4", "#### "), ("H5", "##### "), ("H6", "###### ")]
        
        for text, prefix in header_data:
            btn = Gtk.Button()
            btn.set_label(text)
            btn.add_css_class("header-preview-btn")
            btn.set_size_request(-1, 20)

            def make_header_callback(prefix_val):
                return lambda x: (self.insert_format(prefix_val, ""), popover.popdown())

            btn.connect("clicked", make_header_callback(prefix))
            popover_box.append(btn)
        
        popover.set_child(popover_box)
        headers_button.set_popover(popover)
        return headers_button

    def create_view_buttons(self):
        view_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        view_buttons_box.set_spacing(0)
        
        def create_view_button(icon_name, tooltip):
            btn = Gtk.Button()
            btn.set_icon_name(icon_name)
            btn.set_tooltip_text(tooltip)
            btn.add_css_class("flat")
            btn.add_css_class("super-compact-btn")
            btn.set_size_request(18, 18)
            return btn
        
        self.editor_view_btn = create_view_button("sidebar-collapse-left-symbolic", _("Editor only"))
        self.editor_view_btn.connect("clicked", lambda x: self.set_view_mode("editor"))
        view_buttons_box.append(self.editor_view_btn)

        self.split_view_btn = create_view_button("page-2sides-symbolic", _("Split view"))
        self.split_view_btn.connect("clicked", lambda x: self.set_view_mode("split"))
        self.split_view_btn.add_css_class("view-btn-active")
        view_buttons_box.append(self.split_view_btn)
                    
        self.preview_view_btn = create_view_button("sidebar-collapse-right-symbolic", _("Preview only"))
        self.preview_view_btn.connect("clicked", lambda x: self.set_view_mode("preview"))
        view_buttons_box.append(self.preview_view_btn)
        
        return view_buttons_box

    def create_main_panels(self, main_box):
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_vexpand(True)
        self.paned.set_hexpand(True)
        self.current_view_mode = "split"
        
        self.create_editor_panel()
        
        self.create_preview_panel()
        
        self.setup_scroll_sync()
        
        self.paned.set_position(500)
        main_box.append(self.paned)

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
        
        self.setup_search_tags()
        
        self.setup_editor_events()
        
        self.editor_scroll.set_child(self.text_view)
        self.paned.set_start_child(self.editor_scroll)

    def create_preview_panel(self):
        self.preview_scroll = Gtk.ScrolledWindow()
        self.preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
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
        
        preview_click = Gtk.GestureClick()
        preview_click.connect("pressed", self.on_preview_clicked)
        self.preview_label.add_controller(preview_click)
        
        self.preview_scroll.set_child(self.preview_label)
        self.paned.set_end_child(self.preview_scroll)

    def create_status_bar(self):
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        status_box.add_css_class("toolbar")
        status_box.set_spacing(8)
        status_box.set_margin_start(15)
        status_box.set_margin_end(15)
        status_box.set_margin_top(3)
        status_box.set_margin_bottom(3)
        
        self.doc_status_label = Gtk.Label()
        self.doc_status_label.set_text(_("Ready"))
        self.doc_status_label.add_css_class("dim-label")
        status_box.append(self.doc_status_label)
        
        def add_separator():
            sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            sep.set_margin_top(2)
            sep.set_margin_bottom(2)
            status_box.append(sep)
        
        add_separator()
        
        self.lines_label = Gtk.Label()
        self.lines_label.set_text(f"1 {_('lines')}")
        self.lines_label.add_css_class("dim-label")
        status_box.append(self.lines_label)
        
        add_separator()
        
        self.words_label = Gtk.Label()
        self.words_label.set_text(f"0 {_('words')}")
        self.words_label.add_css_class("dim-label")
        status_box.append(self.words_label)
        
        add_separator()
        
        self.size_label = Gtk.Label()
        self.size_label.set_text("0 B")
        self.size_label.add_css_class("dim-label")
        status_box.append(self.size_label)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        status_box.append(spacer)
        
        self.cursor_label = Gtk.Label()
        self.cursor_label.set_text(f"{_('Line')} 1, {_('Col')} 1")
        self.cursor_label.add_css_class("dim-label")
        status_box.append(self.cursor_label)
        
        add_separator()
        
        self.filetype_label = Gtk.Label()
        self.filetype_label.set_text("Markdown")
        self.filetype_label.add_css_class("dim-label")
        status_box.append(self.filetype_label)
        
        return status_box

    def show_welcome_state(self):
        self.content_stack.set_visible_child_name("welcome")
        self.set_title(_("Markdown Editor"))
        
        for btn_name in ['new_btn', 'open_btn', 'save_btn', 'search_btn']:
            if hasattr(self, btn_name):
                getattr(self, btn_name).set_visible(False)
        
        print_action = self.get_application().lookup_action("print")
        if print_action:
            print_action.set_enabled(False)

    def show_editor_state(self):
        self.content_stack.set_visible_child_name("editor")
        
        for btn_name in ['new_btn', 'open_btn', 'save_btn', 'search_btn']:
            if hasattr(self, btn_name):
                getattr(self, btn_name).set_visible(True)
        
        print_action = self.get_application().lookup_action("print")
        if print_action:
            print_action.set_enabled(True)

    def apply_css(self):
        if not Gtk or not Gdk:
            return
            
        css_provider = Gtk.CssProvider()
        css_data = """
        .welcome-card {
            background-color: @window_bg_color;
            border: 1px solid @borders;
            border-radius: 12px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
            margin: 20px;
            padding: 40px;
        }
        
        .welcome-card:hover {
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
            transition: box-shadow 200ms ease-in-out;
        }
        
        .super-compact-btn {
            min-height: 18px;
            min-width: 18px;
            margin: 1px 2px;
            border-radius: 2px;
            transition: all 80ms ease-in-out;
            border: none;
            box-shadow: none;
            padding: 1px;
            background: transparent;
        }
        
        .super-compact-btn:hover {
            background-color: alpha(@accent_color, 0.15);
        }
        
        .header-preview-btn {
            padding: 0px 8px;
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
        
        .view-btn-active {
            background-color: alpha(@accent_color, 0.2);
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
        }
        
        textview {
            font-family: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        
        label {
            font-family: 'DejaVu Sans', 'Noto Sans', sans-serif;
            font-size: 14px;
            line-height: 1.6;
        }
        
        separator {
            border: none;
            background: alpha(@borders, 0.3);
            min-width: 1px;
            min-height: 1px;
        }
        
        .compact-entry {
            min-height: 24px;
            max-height: 24px;
            padding: 2px 8px;
            margin: 0px;
            font-size: 13px;
        }
        """
        
        css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_shortcuts(self):
        if not Gtk:
            return
            
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
                ("Escape", lambda *args: self.hide_search()),
            ]
            
            for trigger_string, callback in shortcuts:
                shortcut = Gtk.Shortcut()
                shortcut.set_trigger(Gtk.ShortcutTrigger.parse_string(trigger_string))
                shortcut.set_action(Gtk.CallbackAction.new(callback))
                controller.add_shortcut(shortcut)
            
            self.add_controller(controller)
            
        except Exception as e:
            print(f"Error setting up shortcuts: {e}")

    def apply_render_style(self):
        style = self.config.get("render_style", "default")
        
        if style == "github":
            self.renderer = GitHubRenderer()
        elif style == "github-light":
            self.renderer = GitHubLightRenderer()
        elif style == "github-dark":
            self.renderer = GitHubDarkRenderer()
        elif style == "gitlab":
            self.renderer = GitLabRenderer()
        elif style == "splendor":
            self.renderer = SplendorRenderer()
        elif style == "modest":
            self.renderer = ModestRenderer()
        elif style == "retro":
            self.renderer = RetroRenderer()
        elif style == "air":
            self.renderer = AirRenderer()
        else:
            self.renderer = ImprovedRenderer()
        
        if hasattr(self, 'text_buffer'):
            self.update_preview_with_new_style()

    def update_preview_with_new_style(self):
        if not hasattr(self, 'text_buffer'):
            return
            
        text = self.text_buffer.get_text(
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter(),
            False
        )
        
        preview_text = self.renderer.render_text(text)
        try:
            self.preview_label.set_markup(preview_text)
        except Exception as e:
            print(f"Error updating preview: {e}")
            self.preview_label.set_text(text)
    
    def on_close(self, window):
        try:
            if hasattr(self, 'paned'):
                self.config.set("paned_position", self.paned.get_position())
            
            width, height = self.get_default_size()
            self.config.set("window_width", width)
            self.config.set("window_height", height)
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
        
        return False

class MarkdownApp(Adw.Application):
    def __init__(self):
        try:
            super().__init__(
                application_id="com.pabmartine.MarkdownEditor",
                flags=Gio.ApplicationFlags.DEFAULT_FLAGS
            )
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
        
        language_action = Gio.SimpleAction.new_stateful(
            "language", GLib.VariantType.new("s"), GLib.Variant("s", "auto")
        )
        language_action.connect("activate", self.on_language_changed)
        self.add_action(language_action)

        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
    
    def on_print(self, action, parameter):
        if hasattr(self, "win") and hasattr(self.win, 'text_buffer'):
            print_operation = Gtk.PrintOperation()
            print_operation.set_n_pages(1)
            print_operation.connect("draw-page", self.on_draw_page)
            
            try:
                result = print_operation.run(
                    Gtk.PrintOperationAction.PRINT_DIALOG, 
                    self.win
                )
            except Exception as e:
                print(f"Error printing: {e}")
    
    def on_draw_page(self, operation, context, page_num):
        if not hasattr(self.win, 'text_buffer'):
            return
            
        text = self.win.text_buffer.get_text(
            self.win.text_buffer.get_start_iter(),
            self.win.text_buffer.get_end_iter(),
            False
        )
        
        cairo_context = context.get_cairo_context()
        cairo_context.set_font_size(12)
        
        lines = text.split('\n')
        y = 20
        line_height = 15
        
        for line in lines:
            if y > context.get_height() - 20:
                break
            cairo_context.move_to(20, y)
            cairo_context.show_text(line)
            y += line_height
    
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
            
        dialog = Adw.PreferencesWindow()
        dialog.set_title(_("Preferences"))
        dialog.set_modal(True)
        dialog.set_transient_for(self.win)

        page = Adw.PreferencesPage()
        page.set_title(_("General"))

        language_group = self.create_language_preferences()
        page.add(language_group)

        appearance_group = self.create_appearance_preferences()
        page.add(appearance_group)

        render_group = self.create_render_preferences()
        page.add(render_group)

        dialog.add(page)
        dialog.present()

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

        dark_theme_row = Adw.SwitchRow()
        dark_theme_row.set_title(_("Dark Theme"))
        dark_theme_row.set_subtitle(_("Use dark theme for the application"))
        dark_theme_row.set_active(self.win.config.get("dark_theme", False))
        dark_theme_row.connect("notify::active", self.on_theme_changed)
        appearance_group.add(dark_theme_row)
        
        return appearance_group

    def create_render_preferences(self):
        render_group = Adw.PreferencesGroup()
        render_group.set_title(_("Render style"))

        style_row = Adw.ComboRow()
        style_row.set_title(_("Preview style"))
        style_row.set_subtitle(_("Changes the appearance of rendered content"))
        
        style_model = Gtk.StringList()
        style_options = [
            _("Default"),
            _("GitHub"),
            _("GitHub Light"),
            _("GitHub Dark"),
            _("GitLab"),
            _("Splendor"),
            _("Modest"),
            _("Retro"),
            _("Air")
        ]
        
        for option in style_options:
            style_model.append(option)
        
        style_row.set_model(style_model)

        current_style = self.win.config.get("render_style", "default")
        style_codes = ["default", "github", "github-light", "github-dark", 
                      "gitlab", "splendor", "modest", "retro", "air"]
        
        if current_style in style_codes:
            style_row.set_selected(style_codes.index(current_style))
        else:
            style_row.set_selected(0)

        style_row.connect("notify::selected", self.on_render_style_changed)
        render_group.add(style_row)
        
        return render_group

    def on_render_style_changed(self, combo_row, param):
        selected = combo_row.get_selected()
        style_codes = ["default", "github", "github-light", "github-dark", 
                      "gitlab", "splendor", "modest", "retro", "air"]
        
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

    def on_theme_changed(self, switch_row, param):
        dark_theme = switch_row.get_active()
        self.win.apply_theme(dark_theme)
        self.win.config.set("dark_theme", dark_theme)

    def on_about(self, action, parameter):
        if not Adw:
            print("Adwaita not available for About dialog")
            return
            
        about_dialog = Adw.AboutWindow()
        about_dialog.set_transient_for(self.win)
        about_dialog.set_modal(True)
        
        # Set the application icon
        about_dialog.set_application_icon("text-markdown-symbolic")
        
        about_dialog.set_application_name(_("Markdown Editor"))
        about_dialog.set_version("1.1.0")
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
        
        about_dialog.present()
    
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
            
            self.win.present()
            
        except Exception as e:
            print(f"Error activating application: {e}")
            traceback.print_exc()

class MarkdownUtils:
    @staticmethod
    def extract_headers(text):
        headers = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#'):
                level = 0
                for char in stripped:
                    if char == '#':
                        level += 1
                    else:
                        break
                
                if level <= 6:
                    title = stripped[level:].strip()
                    if title:
                        headers.append({
                            'level': level,
                            'title': title,
                            'line': i + 1
                        })
        
        return headers
    
    @staticmethod
    def count_words(text):
        import re
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]*`', '', text)
        
        text = re.sub(r'!?\[[^\]]*\]\([^)]*\)', '', text)
        
        text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]*)\*', r'\1', text)
        text = re.sub(r'~~([^~]*)~~', r'\1', text)
        
        words = [word for word in text.split() if word.strip()]
        return len(words)
    
    @staticmethod
    def estimate_reading_time(text, wpm=200):
        word_count = MarkdownUtils.count_words(text)
        minutes = max(1, round(word_count / wpm))
        return minutes
    
    @staticmethod
    def generate_toc(text):
        headers = MarkdownUtils.extract_headers(text)
        if not headers:
            return ""
        
        toc = [f"## {_('Table of Contents')}\n"]
        
        for header in headers:
            indent = "  " * (header['level'] - 1)
            anchor = header['title'].lower().replace(' ', '-')
            anchor = re.sub(r'[^\w\-]', '', anchor)
            toc.append(f"{indent}- [{header['title']}](#{anchor})")
        
        return "\n".join(toc) + "\n\n"

def run_basic_tests():
    print("Running basic tests...")
    
    test_text = f"""# {_('Main Title')}

## {_('Subtitle')}

{_('This is a test paragraph with')} **{_('bold text')}** {_('and')} *{_('italic text')}*.

- {_('List item')} 1
- {_('List item')} 2

```
{_('Code block')}
```
"""
    
    utils = MarkdownUtils()
    
    headers = utils.extract_headers(test_text)
    assert len(headers) == 2, f"Expected 2 headers, got {len(headers)}"
    assert headers[0]['level'] == 1, f"Expected level 1, got {headers[0]['level']}"
    
    word_count = utils.count_words(test_text)
    assert word_count > 0, "Word count should be greater than 0"
    
    print("✓ All basic tests passed")

class RendererFactory:
    @staticmethod
    def create_renderer(style_name):
        renderers = {
            "default": ImprovedRenderer,
            "github": GitHubRenderer,
            "github-light": GitHubLightRenderer,
            "github-dark": GitHubDarkRenderer,
            "gitlab": GitLabRenderer,
            "splendor": SplendorRenderer,
            "modest": ModestRenderer,
            "retro": RetroRenderer,
            "air": AirRenderer,
        }
        
        renderer_class = renderers.get(style_name, ImprovedRenderer)
        return renderer_class()
    
    @staticmethod
    def get_available_styles():
        return [
            "default", "github", "github-light", "github-dark",
            "gitlab", "splendor", "modest", "retro", "air"
        ]

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
        try:
            desktop_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(desktop_dir, exist_ok=True)
            
            desktop_file = os.path.join(desktop_dir, "markdown-editor.desktop")
            
            content = self.desktop_file_content.format(script_path=script_path)
            
            with open(desktop_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            os.chmod(desktop_file, 0o755)
            
            print(f"Desktop file installed at: {desktop_file}")
            return True
            
        except Exception as e:
            print(f"Error installing desktop file: {e}")
            return False
    
    def check_dependencies(self):
        dependencies = {
            'gtk': ('gi.repository', 'Gtk'),
            'adwaita': ('gi.repository', 'Adw'),
            'pango': ('gi.repository', 'Pango'),
            'gdk': ('gi.repository', 'Gdk'),
            'glib': ('gi.repository', 'GLib'),
            'gio': ('gi.repository', 'Gio'),
        }
        
        optional_deps = {
            'markdown': ('markdown', None),
        }
        
        print("Checking dependencies...")
        
        all_ok = True
        for name, (module, attr) in dependencies.items():
            try:
                if attr:
                    mod = __import__(module, fromlist=[attr])
                    getattr(mod, attr)
                else:
                    __import__(module)
                print(f"✓ {name}: OK")
            except ImportError:
                print(f"✗ {name}: MISSING")
                all_ok = False
        
        print("\nOptional dependencies:")
        for name, (module, attr) in optional_deps.items():
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
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        except:
            print("PyGObject: Not available")
        
        print("================================")
    
    @staticmethod
    def run_performance_test():
        import time
        
        print("Running performance test...")
        
        test_text = f"# {_('Test')}\n\n" + f"{_('Test paragraph')}. " * 100
        renderer = ImprovedRenderer()
        
        start_time = time.time()
        for _ in range(100):
            rendered = renderer.render_text(test_text)
        end_time = time.time()
        
        print(f"Rendering (100 iterations): {end_time - start_time:.3f}s")
        
        utils = MarkdownUtils()
        start_time = time.time()
        for _ in range(1000):
            word_count = utils.count_words(test_text)
        end_time = time.time()
        
        print(f"Word counting (1000 iterations): {end_time - start_time:.3f}s")

def parse_command_line_args():
    import argparse
    
    parser = argparse.ArgumentParser(description=_("Advanced Markdown Editor"))
    parser.add_argument('files', nargs='*', help=_('Files to open'))
    parser.add_argument('--vim', action='store_true', help=_('Start in Vim mode'))
    parser.add_argument('--theme', choices=['default', 'dark', 'monokai'], 
                       help=_('Editor theme'))
    parser.add_argument('--auto-save', type=int, metavar='SECONDS',
                       help=_('Enable auto-save with interval in seconds'))
    parser.add_argument('--version', action='version', version='1.1.0')
    parser.add_argument('--debug', action='store_true', help=_('Enable debug mode'))
    parser.add_argument('--install-desktop', action='store_true', help=_('Install desktop file'))
    parser.add_argument('--test', action='store_true', help=_('Run tests'))
    
    return parser.parse_args()

def apply_cli_options(app, args):
    if hasattr(app, 'win') and app.win:
        if args.theme:
            app.win.config.set('render_style', args.theme)
            app.win.apply_render_style()
        
        if args.vim:
            app.win.config.set('vim_mode', True)
        
        for file_path in args.files:
            if os.path.exists(file_path):
                app.win.load_file(file_path)
                break

def main_complete():
    try:
        args = parse_command_line_args()
    except SystemExit:
        return 0
    
    if hasattr(args, 'debug') and args.debug:
        DebugUtils.print_system_info()
        DebugUtils.enable_debug_logging()
    
    installer = SystemInstaller()
    if not installer.check_dependencies():
        print(f"\n{_('ERROR: Missing required dependencies.')}")
        print(_("Check the installation guide for more information."))
        return 1
    
    if hasattr(args, 'install_desktop') and args.install_desktop:
        script_path = os.path.abspath(__file__)
        if installer.install_desktop_file(script_path):
            print(_("System integration completed."))
        return 0
    
    if hasattr(args, 'test') and args.test:
        run_basic_tests()
        DebugUtils.run_performance_test()
        return 0
    
    try:
        app = MarkdownApp()
        if hasattr(args, 'files'):
            apply_cli_options(app, args)
        result = app.run(sys.argv)
        return result
        
    except KeyboardInterrupt:
        print(f"\n{_('Application interrupted by user.')}")
        return 0
    except Exception as e:
        print(f"{_('Fatal error in application')}: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    if sys.version_info < (3, 6):
        print(_("ERROR: Python 3.6 or higher required"))
        sys.exit(1)
    
    sys.exit(main_complete())                                                