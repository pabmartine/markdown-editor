import re
from html.parser import HTMLParser

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    import gi
    gi.require_version("GLib", "2.0")
    from gi.repository import GLib
except Exception:
    GLib = None

from ..core.i18n import translate as _


class ImprovedRenderer:
    def __init__(self):
        self.style = "default"

    @staticmethod
    def _strip_optional_closing_hashes(text):
        if not text:
            return text
        return re.sub(r'\s+#+\s*$', '', text.rstrip())

    def get_markdown_extensions(self):
        return [
            'tables',
            'fenced_code',
            'sane_lists',
        ]

    def render_text(self, markdown_text):
        try:
            if MARKDOWN_AVAILABLE:
                html = markdown.markdown(markdown_text, extensions=self.get_markdown_extensions())
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
                self.list_types = []
                self.ol_counters = []
                self.in_code_block = False
                self.table_column = 0
                self.in_heading_level = None
                self.style = style
                self.pending_li_content = None

            def flush_pending_li(self):
                if self.pending_li_content:
                    indent, bullet = self.pending_li_content
                    
                    if self.style == "slate" or self.style == "ivory":
                        bullet = f'<span foreground="#1f2328">{bullet}</span>'
                    elif self.style == "nocturne":
                        bullet = f'<span foreground="#f0f6fc">{bullet}</span>'
                    elif self.style == "ember":
                        bullet = f'<span foreground="#171321">{bullet}</span>'
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
                    if self.style == "slate":
                        self.output.append('\n<span size="28000" weight="600" foreground="#1f2328">')
                    elif self.style == "ivory":
                        self.output.append('\n<span size="28000" weight="600" foreground="#1f2328">')
                    elif self.style == "nocturne":
                        self.output.append('\n<span size="28000" weight="600" foreground="#f0f6fc">')
                    elif self.style == "ember":
                        self.output.append('\n<span size="26000" weight="bold" foreground="#171321">')
                    elif self.style == "splendor":
                        self.output.append('\n<span size="30000" weight="300" foreground="#2c3e50">')
                    elif self.style == "modest":
                        self.output.append('\n<span size="25000" weight="bold" foreground="#333">')
                    elif self.style == "retro":
                        self.output.append('\n<span size="27000" weight="bold" foreground="#8b4513">')
                    elif self.style == "air":
                        self.output.append('\n<span size="28000" weight="300" foreground="#2aa198">')
                    else:
                        self.output.append('\n<span size="22000" weight="bold">')
                elif tag == 'h2':
                    self.in_heading_level = 2
                    if self.style == "slate":
                        self.output.append('\n<span size="23000" weight="600" foreground="#1f2328">')
                    elif self.style == "ivory":
                        self.output.append('\n<span size="23000" weight="600" foreground="#1f2328">')
                    elif self.style == "nocturne":
                        self.output.append('\n<span size="23000" weight="600" foreground="#f0f6fc">')
                    elif self.style == "ember":
                        self.output.append('\n<span size="22000" weight="bold" foreground="#171321">')
                    elif self.style == "splendor":
                        self.output.append('\n<span size="24000" weight="400" foreground="#34495e">')
                    elif self.style == "modest":
                        self.output.append('\n<span size="22000" weight="bold" foreground="#444">')
                    elif self.style == "retro":
                        self.output.append('\n<span size="23000" weight="bold" foreground="#a0522d">')
                    elif self.style == "air":
                        self.output.append('\n<span size="23000" weight="400" foreground="#268bd2">')
                    else:
                        self.output.append('\n<span size="19000" weight="bold">')
                elif tag == 'h3':
                    self.in_heading_level = 3
                    size = "19500" if self.style == "slate" else "19000" if self.style == "ember" else "18500"
                    self.output.append(f'\n<span size="{size}" weight="bold">')
                elif tag == 'h4':
                    self.in_heading_level = 4
                    size = "17500" if self.style == "slate" else "17000" if self.style == "ember" else "16000"
                    self.output.append(f'\n<span size="{size}" weight="bold">')
                elif tag == 'h5':
                    self.in_heading_level = 5
                    size = "16000" if self.style == "slate" else "15500" if self.style == "ember" else "14500"
                    self.output.append(f'\n<span size="{size}" weight="bold">')
                elif tag == 'h6':
                    self.in_heading_level = 6
                    size = "14500" if self.style == "slate" else "14000" if self.style == "ember" else "13000"
                    self.output.append(f'\n<span size="{size}" weight="bold">')
                elif tag == 'strong' or tag == 'b':
                    if self.style == "slate" or self.style == "ivory":
                        self.output.append('<span weight="600" foreground="#1f2328">')
                    elif self.style == "nocturne":
                        self.output.append('<span weight="600" foreground="#f0f6fc">')
                    elif self.style == "ember":
                        self.output.append('<span weight="bold" foreground="#171321">')
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
                    if self.style == "slate" or self.style == "ivory":
                        self.output.append('<span style="italic" foreground="#24292f">')
                    elif self.style == "nocturne":
                        self.output.append('<span style="italic" foreground="#8b949e">')
                    elif self.style == "ember":
                        self.output.append('<span style="italic" foreground="#74717a">')
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
                        if self.style == "slate":
                            self.output.append('<span font_family="monospace" background="#afb8c133" foreground="#24292f" size="small"> ')
                        elif self.style == "ivory":
                            self.output.append('<span font_family="monospace" background="#afb8c133" foreground="#24292f" size="small"> ')
                        elif self.style == "nocturne":
                            self.output.append('<span font_family="monospace" background="#6e768166" foreground="#e6edf3" size="small"> ')
                        elif self.style == "ember":
                            self.output.append('<span font_family="monospace" background="#ececef" foreground="#171321" size="small"> ')
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
                    if self.style == "slate":
                        self.output.append('\n<span font_family="monospace" background="#f6f8fa" foreground="#24292f">')
                    elif self.style == "ivory":
                        self.output.append('\n<span font_family="monospace" background="#f6f8fa" foreground="#24292f">')
                    elif self.style == "nocturne":
                        self.output.append('\n<span font_family="monospace" background="#161b22" foreground="#e6edf3">')
                    elif self.style == "ember":
                        self.output.append('\n<span font_family="monospace" background="#fbfafd" foreground="#171321">')
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
                    if self.style == "slate" or self.style == "ivory":
                        self.output.append('\n<span foreground="#d1d9e0">' + '─' * 50 + '</span>\n')
                    elif self.style == "nocturne":
                        self.output.append('\n<span foreground="#30363d">' + '─' * 60 + '</span>\n')
                    elif self.style == "ember":
                        self.output.append('\n<span foreground="#dcdcde">' + '─' * 60 + '</span>\n')
                    elif self.style == "splendor":
                        self.output.append('\n<span foreground="#bdc3c7">' + '╌' * 50 + '</span>\n')
                    elif self.style == "retro":
                        self.output.append('\n<span foreground="#cd853f">' + '╌' * 50 + '</span>\n')
                    else:
                        self.output.append('\n' + '─' * 50 + '\n')
                elif tag == 'blockquote':
                    if self.style == "slate" or self.style == "ivory":
                        self.output.append('\n<span foreground="#59636e">│ ')
                    elif self.style == "nocturne":
                        self.output.append('\n<span foreground="#8b949e">│ ')
                    elif self.style == "ember":
                        self.output.append('\n<span foreground="#74717a">│ ')
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
                    self.list_types.append('ul')
                    self.output.append('\n')
                elif tag == 'ol':
                    self.list_level += 1
                    self.list_types.append('ol')
                    self.ol_counters.append(0)
                    self.output.append('\n')
                elif tag == 'li':
                    indent = '  ' * (self.list_level - 1)
                    current_list = self.list_types[-1] if self.list_types else 'ul'
                    if current_list == 'ol':
                        self.ol_counters[-1] += 1
                        bullet = f"{self.ol_counters[-1]}. "
                    else:
                        bullet = "• "
                    self.pending_li_content = (indent, bullet)
                elif tag == 'del' or tag == 's':
                    self.output.append('<s>')
                elif tag == 'a':
                    href = next((value for name, value in attrs if name == 'href'), '#')
                    href = href.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
                    if self.style == "slate" or self.style == "ivory":
                        self.output.append(f'<a href="{href}"><span foreground="#0969da" underline="single">')
                    elif self.style == "nocturne":
                        self.output.append(f'<a href="{href}"><span foreground="#58a6ff" underline="single">')
                    elif self.style == "ember":
                        self.output.append(f'<a href="{href}"><span foreground="#1f75cb" underline="single" weight="medium">')
                    elif self.style == "splendor":
                        self.output.append(f'<a href="{href}"><span foreground="#3498db" underline="single">')
                    elif self.style == "modest":
                        self.output.append(f'<a href="{href}"><span foreground="#337ab7" underline="single">')
                    elif self.style == "retro":
                        self.output.append(f'<a href="{href}"><span foreground="#268bd2" underline="single">')
                    elif self.style == "air":
                        self.output.append(f'<a href="{href}"><span foreground="#268bd2" underline="single">')
                    else:
                        self.output.append(f'<a href="{href}"><span foreground="blue" underline="single">')
                elif tag == 'img':
                    alt = next((value for name, value in attrs if name == 'alt'), _('Image'))
                    alt = GLib.markup_escape_text(alt)
                    image_label = GLib.markup_escape_text(_("Image"))
                    self.output.append(f'\n🖼️ [{image_label}: {alt}]\n')
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
                        if self.style == "slate":
                            self.output.append('<span foreground="#d1d9e0">' + '─' * 60 + '</span>\n')
                        elif self.style == "ember":
                            self.output.append('<span foreground="#d1d0d3">' + '─' * 60 + '</span>\n')
                        else:
                            self.output.append('<span foreground="#c9c9c9">' + '─' * 60 + '</span>\n')
                    elif self.in_heading_level == 2:
                        if self.style == "slate":
                            self.output.append('<span foreground="#d1d9e0">' + '─' * 50 + '</span>\n')
                        elif self.style == "ember":
                            self.output.append('<span foreground="#e3e3e3">' + '─' * 50 + '</span>\n')
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
                    if self.style == "default":
                        self.output.append(' "</span>\n')
                    else:
                        self.output.append('</span>\n')
                elif tag == 'ul' or tag == 'ol':
                    self.list_level -= 1
                    if self.list_types:
                        ended_list = self.list_types.pop()
                        if ended_list == 'ol' and self.ol_counters:
                            self.ol_counters.pop()
                    self.output.append('\n')
                elif tag == 'li':
                    self.output.append('\n')
                elif tag == 'a':
                    self.output.append('</span></a>')
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
                        
                        if self.style == "slate" or self.style == "ivory":
                            checkbox = f'<span foreground="#1f2328">{checkbox}</span>'
                        elif self.style == "nocturne":
                            checkbox = f'<span foreground="#f0f6fc">{checkbox}</span>'
                        elif self.style == "ember":
                            checkbox = f'<span foreground="#171321">{checkbox}</span>'
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
                processed = self._process_inline_format(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="24000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="20000" weight="bold">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19500" weight="bold">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17500" weight="bold">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="16000" weight="bold">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14500" weight="bold">{processed}</span>')
                result.append('')
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
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="blue" underline="single">\1</span></a>', processed)
        
        return processed

class SlateRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "slate"

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
                    result.append('<span font_family="SFMono-Regular,Consolas" background="#edf1f5" foreground="#364152">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_slate(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="28000" weight="600" foreground="#364152">{processed}</span>')
                result.append('<span foreground="#cbd2dc">' + '─' * 60 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_slate(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="23000" weight="600" foreground="#364152">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format_slate(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19500" weight="600" foreground="#48606f">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format_slate(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17500" weight="600" foreground="#48606f">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format_slate(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="16000" weight="600" foreground="#5b6574">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format_slate(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14500" weight="600" foreground="#667085">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_slate(stripped_line[2:])
                result.append(f'<span foreground="#667085">│ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_slate(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_slate(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="600" foreground="#364152">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#5b6574">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="SFMono-Regular" background="#d8dee633" foreground="#48606f" size="small"> \1 </span>', processed)
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="#5f6b7a" underline="single">\1</span></a>', processed)
        return processed

class IvoryRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "ivory"

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
                    result.append('<span font_family="SFMono-Regular,Consolas" background="#f7f1e8" foreground="#7c5c45">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_ivory(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="28000" weight="600" foreground="#7c5c45">{processed}</span>')
                result.append('<span foreground="#e3dccd">' + '─' * 60 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_ivory(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="23000" weight="600" foreground="#7c5c45">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format_ivory(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19500" weight="600" foreground="#8c5e34">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format_ivory(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17500" weight="600" foreground="#8c5e34">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format_ivory(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="16000" weight="600" foreground="#a17c5b">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format_ivory(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14500" weight="600" foreground="#7c6f64">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_ivory(stripped_line[2:])
                result.append(f'<span foreground="#7c6f64">│ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_ivory(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_ivory(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="600" foreground="#7c5c45">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#8c5e34">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="SFMono-Regular" background="#eadfce88" foreground="#8b7355" size="small"> \1 </span>', processed)
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="#a17c5b" underline="single">\1</span></a>', processed)
        return processed

class NocturneRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "nocturne"

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
                    result.append('<span font_family="SFMono-Regular,Consolas" background="#0b1220" foreground="#dbe7f5">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_nocturne(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="28000" weight="600" foreground="#dbe7f5">{processed}</span>')
                result.append('<span foreground="#243042">' + '─' * 60 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_nocturne(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="23000" weight="600" foreground="#dbe7f5">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format_nocturne(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19500" weight="600" foreground="#c4d4ea">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format_nocturne(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17500" weight="600" foreground="#c4d4ea">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format_nocturne(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="16000" weight="600" foreground="#94a3b8">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format_nocturne(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14500" weight="600" foreground="#7c8aa0">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_nocturne(stripped_line[2:])
                result.append(f'<span foreground="#94a3b8">│ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_nocturne(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_nocturne(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="600" foreground="#dbe7f5">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#94a3b8">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="SFMono-Regular" background="#243042aa" foreground="#a7f3d0" size="small"> \1 </span>', processed)
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="#7dd3fc" underline="single">\1</span></a>', processed)
        return processed

class EmberRenderer(ImprovedRenderer):
    def __init__(self):
        super().__init__()
        self.style = "ember"

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
                    result.append('<span font_family="JetBrains Mono,Consolas" background="#f7ede2" foreground="#8b4e3d">')
                else:
                    result.append('</span>')
                continue
            
            if in_code_block:
                escaped = stripped_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(escaped)
                continue
            
            if stripped_line.startswith('# '):
                processed = self._process_inline_format_ember(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="26000" weight="600" foreground="#8b4e3d">{processed}</span>')
                result.append('<span foreground="#e7d6c4">' + '─' * 60 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_ember(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="22000" weight="600" foreground="#8b4e3d">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format_ember(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19000" weight="600" foreground="#a44a3f">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format_ember(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17000" weight="600" foreground="#a44a3f">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format_ember(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="15500" weight="600" foreground="#b7795e">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format_ember(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14000" weight="600" foreground="#8a6a5b">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('> '):
                processed = self._process_inline_format_ember(stripped_line[2:])
                result.append(f'<span foreground="#8a6a5b">│ {processed}</span>')
            else:
                if stripped_line:
                    processed = self._process_inline_format_ember(stripped_line)
                    result.append(processed)
                else:
                    result.append('')
        
        if in_code_block:
            result.append('</span>')
        
        return '\n'.join(result)
    
    def _process_inline_format_ember(self, text):
        if not text:
            return text
        processed = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'<span weight="600" foreground="#8b4e3d">\1</span>', processed)
        processed = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<span style="italic" foreground="#8a6a5b">\1</span>', processed)
        processed = re.sub(r'`([^`\n]+?)`', r'<span font_family="JetBrains Mono" background="#f1ddcc" foreground="#a44a3f" size="small"> \1 </span>', processed)
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="#c97b63" underline="single" weight="medium">\1</span></a>', processed)
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
                processed = self._process_inline_format_splendor(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="30000" weight="300" foreground="#2c3e50">{processed}</span>')
                result.append('<span foreground="#bdc3c7">' + '╌' * 50 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_splendor(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="24000" weight="400" foreground="#34495e">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format_splendor(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19000" weight="500" foreground="#4a6072">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format_splendor(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17000" weight="500" foreground="#5d7283">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format_splendor(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="15500" weight="500" foreground="#708494">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format_splendor(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14000" weight="500" foreground="#7f8c8d">{processed}</span>')
                result.append('')
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
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="#3498db" underline="single">\1</span></a>', processed)
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
                processed = self._process_inline_format_modest(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="25000" weight="bold" foreground="#333">{processed}</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_modest(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="22000" weight="bold" foreground="#444">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format_modest(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19000" weight="bold" foreground="#555">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format_modest(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17000" weight="bold" foreground="#666">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format_modest(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="15500" weight="bold" foreground="#777">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format_modest(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14000" weight="bold" foreground="#888">{processed}</span>')
                result.append('')
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
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="#337ab7" underline="single">\1</span></a>', processed)
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
                processed = self._process_inline_format_retro(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="27000" weight="bold" foreground="#8b4513">{processed}</span>')
                result.append('<span foreground="#cd853f">' + '╌' * 50 + '</span>')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_retro(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="23000" weight="bold" foreground="#a0522d">{processed}</span>')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format_retro(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19000" weight="bold" foreground="#b5651d">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format_retro(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17000" weight="bold" foreground="#a67c52">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format_retro(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="15500" weight="bold" foreground="#8b7355">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format_retro(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14000" weight="bold" foreground="#7f6a53">{processed}</span>')
                result.append('')
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
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="#268bd2" underline="single">\1</span></a>', processed)
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
                processed = self._process_inline_format_air(self._strip_optional_closing_hashes(stripped_line[2:]))
                result.append(f'<span size="28000" weight="300" foreground="#2aa198">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('## '):
                processed = self._process_inline_format_air(self._strip_optional_closing_hashes(stripped_line[3:]))
                result.append(f'<span size="23000" weight="400" foreground="#268bd2">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('### '):
                processed = self._process_inline_format_air(self._strip_optional_closing_hashes(stripped_line[4:]))
                result.append(f'<span size="19000" weight="500" foreground="#2f8fbe">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('#### '):
                processed = self._process_inline_format_air(self._strip_optional_closing_hashes(stripped_line[5:]))
                result.append(f'<span size="17000" weight="500" foreground="#4f9db0">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('##### '):
                processed = self._process_inline_format_air(self._strip_optional_closing_hashes(stripped_line[6:]))
                result.append(f'<span size="15500" weight="500" foreground="#6ca6a6">{processed}</span>')
                result.append('')
            elif stripped_line.startswith('###### '):
                processed = self._process_inline_format_air(self._strip_optional_closing_hashes(stripped_line[7:]))
                result.append(f'<span size="14000" weight="500" foreground="#7aa3a3">{processed}</span>')
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
        processed = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', processed)
        processed = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2"><span foreground="#268bd2" underline="single">\1</span></a>', processed)
        return processed


class RendererFactory:
    STYLE_ALIASES = {
        "github": "slate",
        "github-light": "ivory",
        "github-dark": "nocturne",
        "gitlab": "ember",
    }

    @staticmethod
    def normalize_style_name(style_name):
        return RendererFactory.STYLE_ALIASES.get(style_name, style_name)

    @staticmethod
    def create_renderer(style_name):
        style_name = RendererFactory.normalize_style_name(style_name)
        renderers = {
            "default": ImprovedRenderer,
            "slate": SlateRenderer,
            "ivory": IvoryRenderer,
            "nocturne": NocturneRenderer,
            "ember": EmberRenderer,
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
            "default", "slate", "ivory", "nocturne",
            "ember", "splendor", "modest", "retro", "air"
        ]
