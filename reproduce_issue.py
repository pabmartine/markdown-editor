
import re

class ImprovedRenderer:
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

renderer = ImprovedRenderer()
text = """# Header
Text with **bold** and *italic*.
- Item 1
- Item 2

> Quote

```
Code block
"""
print(renderer._basic_render(text))

