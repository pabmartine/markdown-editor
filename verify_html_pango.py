
import re
from html.parser import HTMLParser

# Mock translation
def _(text): return text

MARKDOWN_AVAILABLE = True

class ImprovedRenderer:
    def __init__(self):
        self.style = "github"

    def render_text(self, markdown_text):
        # We will mock the markdown output for testing _html_to_pango
        # This simulates what markdown.markdown() would return for complex input
        html = """
        <h1>Header 1</h1>
        <p>Text with <strong>bold</strong> and <em>italic</em>.</p>
        <p>Text with <del>strikethrough</del>.</p>
        <ul>
        <li><p>Item 1</p></li>
        <li><p>Item 2</p></li>
        </ul>
        <ol>
        <li><p>Ordered 1</p></li>
        </ol>
        <pre><code>Code block
</code></pre>
        <blockquote>
        <p>Quote</p>
        </blockquote>
        <hr />
        """
        return self._html_to_pango(html)
    
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
                    if btype == 'ul':
                        self.output.append(f'{indent}• ')
                    elif btype == 'ol':
                        self.output.append(f'{indent}1. ')
                    self.pending_li_content = None

            def handle_starttag(self, tag, attrs):
                if tag != 'li':
                    self.flush_pending_li()
                    
                self.tag_stack.append(tag)
                
                if tag == 'h1':
                    self.in_heading_level = 1
                    if self.style == "github":
                        self.output.append('\n<span size="28000" weight="bold" foreground="#1f2328">')
                    else:
                        self.output.append('\n<span size="24000" weight="bold">')
                elif tag == 'p':
                    # Avoid adding newline if we just added a bullet or number
                    is_after_bullet = False
                    if self.output:
                        last = self.output[-1].rstrip()
                        if last.endswith('•') or (last and last[-1] == '.' and last[:-1].isdigit()):
                            is_after_bullet = True
                            
                    if self.output and not self.output[-1].endswith('\n') and not is_after_bullet:
                        self.output.append('\n')
                elif tag == 'strong' or tag == 'b':
                    if self.style == "github":
                        self.output.append('<span weight="bold" foreground="#1f2328">')
                    else:
                        self.output.append('<b>')
                elif tag == 'em' or tag == 'i':
                    if self.style == "github":
                        self.output.append('<span style="italic" foreground="#656d76">')
                    else:
                        self.output.append('<i>')
                elif tag == 'del' or tag == 's':
                    self.output.append('<s>')
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

            def handle_endtag(self, tag):
                self.flush_pending_li()
                
                if self.tag_stack and self.tag_stack[-1] == tag:
                    self.tag_stack.pop()
                
                if tag == 'h1':
                    self.output.append('</span>\n')
                    if self.in_heading_level == 1:
                        if self.style == "github":
                            self.output.append('<span foreground="#d0d7de">' + '─' * 60 + '</span>\n')
                    self.in_heading_level = None
                elif tag == 'p':
                    self.output.append('\n')
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
                elif tag == 'del' or tag == 's':
                    self.output.append('</s>')
                elif tag == 'ul' or tag == 'ol':
                    self.list_level -= 1
                    self.output.append('\n')
                elif tag == 'li':
                    self.output.append('\n')
                
            def handle_data(self, data):
                if self.pending_li_content:
                    self.flush_pending_li()
                
                data = data.replace('&', '&amp;')
                data = data.replace('<', '&lt;')
                data = data.replace('>', '&gt;')
                self.output.append(data)
                
            def get_pango(self):
                self.flush_pending_li()
                result = ''.join(self.output)
                result = re.sub(r'\n{3,}', '\n\n', result)
                return result.strip()
        
        parser = HTMLToPangoParser(self.style)
        parser.feed(html)
        return parser.get_pango()

renderer = ImprovedRenderer()
print(renderer.render_text("test"))
