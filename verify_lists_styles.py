
import re
from html.parser import HTMLParser

# Mock translation
def _(text): return text

MARKDOWN_AVAILABLE = True

class ImprovedRenderer:
    def __init__(self, style="default"):
        self.style = style

    def render_text(self, markdown_text):
        # Mocking markdown list output
        html = """
        <ul>
        <li><p>Unordered List Item</p></li>
        </ul>
        <ol>
        <li><p>Ordered List Item</p></li>
        </ol>
        """
        return self._html_to_pango(html)
    
    # ... (Pasting the exact _html_to_pango method from markdown-editor.py) ...
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
                
                # ... (rest of handle_starttag as per last successful update) ...
                if tag == 'h1': pass # Simplified for brevity
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
                elif tag == 'p':
                    # Avoid adding newline if we just added a bullet or number
                    is_after_bullet = False
                    if self.output:
                        last = self.output[-1].rstrip()
                        if last.endswith('•') or (last and last[-1] == '.' and last[:-1].isdigit()):
                            is_after_bullet = True
                            
                    if self.output and not self.output[-1].endswith('\n') and not is_after_bullet:
                        self.output.append('\n')

            def handle_endtag(self, tag):
                self.flush_pending_li()
                if self.tag_stack and self.tag_stack[-1] == tag:
                    self.tag_stack.pop()
                
                if tag == 'ul' or tag == 'ol':
                    self.list_level -= 1
                    self.output.append('\n')
                elif tag == 'li':
                    self.output.append('\n')
                elif tag == 'p':
                    self.output.append('\n')
                
            def handle_data(self, data):
                if self.pending_li_content:
                    # simplified data handling for lists
                    indent, _ = self.pending_li_content
                    self.flush_pending_li()
                
                data = data.replace('&', '&amp;')
                self.output.append(data)
                
            def get_pango(self):
                self.flush_pending_li()
                result = ''.join(self.output)
                return result.strip()
        
        parser = HTMLToPangoParser(self.style)
        parser.feed(html)
        return parser.get_pango()

styles = ["default", "github", "gitlab"]
for style in styles:
    renderer = ImprovedRenderer(style)
    print(f"--- Style: {style} ---")
    print(renderer.render_text("list test"))
    print("-" * 20)
