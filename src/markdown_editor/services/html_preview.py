import html
import os
import re
from pathlib import Path

try:
    from markdown_it import MarkdownIt
    MARKDOWN_IT_AVAILABLE = True
except Exception:
    MarkdownIt = None
    MARKDOWN_IT_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except Exception:
    markdown = None
    MARKDOWN_AVAILABLE = False


HTML_THEMES = {
    "default": {
        "page_bg": "#f6f8fb",
        "panel_bg": "#ffffff",
        "text": "#1f2328",
        "muted": "#59636e",
        "border": "#d0d7de",
        "link": "#0969da",
        "code_bg": "#f6f8fa",
        "code_text": "#24292f",
        "quote_bg": "#f6f8fa",
        "quote_border": "#d0d7de",
        "table_header": "#f3f4f6",
        "selection": "rgba(9, 105, 218, 0.16)",
        "body_font": '"Noto Sans", "DejaVu Sans", sans-serif',
        "heading_font": '"Noto Sans", "DejaVu Sans", sans-serif',
        "article_padding": "28px 34px 40px",
        "article_radius": "18px",
        "article_border": "1px solid rgba(208, 215, 222, 0.9)",
        "article_shadow": "0 18px 42px rgba(15, 23, 42, 0.05)",
        "h1_color": "#111827",
        "h2_color": "#1f2937",
        "h1_letter_spacing": "-0.03em",
        "h1_transform": "none",
        "link_weight": "600",
        "link_underline": "none",
        "blockquote_radius": "10px",
        "code_border": "1px solid rgba(208, 215, 222, 0.9)",
        "table_radius": "12px",
    },
    "slate": {
        "page_bg": "#eef2f6",
        "panel_bg": "#fbfdff",
        "text": "#314152",
        "muted": "#6b7a89",
        "border": "#c7d2de",
        "link": "#245d8f",
        "code_bg": "#e6edf5",
        "code_text": "#314152",
        "quote_bg": "#edf3f8",
        "quote_border": "#7c93aa",
        "table_header": "#dde6ef",
        "selection": "rgba(36, 93, 143, 0.16)",
        "body_font": '"IBM Plex Sans", "Noto Sans", sans-serif',
        "heading_font": '"IBM Plex Sans", "Noto Sans", sans-serif',
        "article_padding": "30px 36px 42px",
        "article_radius": "22px",
        "article_border": "1px solid rgba(199, 210, 222, 0.95)",
        "article_shadow": "0 22px 50px rgba(100, 116, 139, 0.12)",
        "h1_color": "#223243",
        "h2_color": "#314152",
        "h1_letter_spacing": "-0.04em",
        "h1_transform": "none",
        "link_weight": "600",
        "link_underline": "none",
        "blockquote_radius": "14px",
        "code_border": "1px solid rgba(199, 210, 222, 0.95)",
        "table_radius": "14px",
    },
    "ivory": {
        "page_bg": "#fffaf2",
        "panel_bg": "#fffdf8",
        "text": "#7c5c45",
        "muted": "#7c6f64",
        "border": "#e3dccd",
        "link": "#9a6c2f",
        "code_bg": "#f7f1e8",
        "code_text": "#7c5c45",
        "quote_bg": "#fffaf2",
        "quote_border": "#b08968",
        "table_header": "#f5efe4",
        "selection": "rgba(176, 137, 104, 0.18)",
        "body_font": 'Georgia, "Noto Serif", serif',
        "heading_font": '"Cormorant Garamond", Georgia, serif',
        "article_padding": "34px 44px 48px",
        "article_radius": "20px",
        "article_border": "1px solid rgba(227, 220, 205, 0.96)",
        "article_shadow": "0 12px 30px rgba(122, 92, 69, 0.08)",
        "h1_color": "#5f4634",
        "h2_color": "#6f533e",
        "h1_letter_spacing": "0.01em",
        "h1_transform": "none",
        "link_weight": "500",
        "link_underline": "underline",
        "blockquote_radius": "4px",
        "code_border": "1px solid rgba(227, 220, 205, 0.96)",
        "table_radius": "6px",
    },
    "nocturne": {
        "page_bg": "#07111f",
        "panel_bg": "#0f1a2b",
        "text": "#dbe7f5",
        "muted": "#92a6bf",
        "border": "#1d3048",
        "link": "#7dd3fc",
        "code_bg": "#09101b",
        "code_text": "#dbe7f5",
        "quote_bg": "#0d1727",
        "quote_border": "#38bdf8",
        "table_header": "#142237",
        "selection": "rgba(56, 189, 248, 0.22)",
        "body_font": '"Inter", "Noto Sans", sans-serif',
        "heading_font": '"Space Grotesk", "Inter", sans-serif',
        "article_padding": "30px 34px 42px",
        "article_radius": "18px",
        "article_border": "1px solid rgba(29, 48, 72, 0.98)",
        "article_shadow": "0 24px 60px rgba(2, 6, 23, 0.45)",
        "h1_color": "#f8fbff",
        "h2_color": "#c7d8ea",
        "h1_letter_spacing": "-0.045em",
        "h1_transform": "none",
        "link_weight": "600",
        "link_underline": "none",
        "blockquote_radius": "12px",
        "code_border": "1px solid rgba(29, 48, 72, 0.98)",
        "table_radius": "12px",
    },
    "ember": {
        "page_bg": "#fdf1e6",
        "panel_bg": "#fffaf4",
        "text": "#7f3f2d",
        "muted": "#9a7059",
        "border": "#ebcfba",
        "link": "#b94d26",
        "code_bg": "#f6e2d2",
        "code_text": "#7f3f2d",
        "quote_bg": "#fff0e4",
        "quote_border": "#d26b42",
        "table_header": "#f7e7d9",
        "selection": "rgba(210, 107, 66, 0.18)",
        "body_font": '"Source Serif 4", Georgia, serif',
        "heading_font": '"Fraunces", "Source Serif 4", serif',
        "article_padding": "32px 40px 46px",
        "article_radius": "16px",
        "article_border": "1px solid rgba(235, 207, 186, 0.98)",
        "article_shadow": "0 18px 42px rgba(185, 77, 38, 0.08)",
        "h1_color": "#6f2f1f",
        "h2_color": "#8f462d",
        "h1_letter_spacing": "-0.03em",
        "h1_transform": "none",
        "link_weight": "600",
        "link_underline": "none",
        "blockquote_radius": "14px",
        "code_border": "1px solid rgba(235, 207, 186, 0.98)",
        "table_radius": "10px",
    },
    "splendor": {
        "page_bg": "#f5f8fb",
        "panel_bg": "#ffffff",
        "text": "#23384a",
        "muted": "#6f7f8d",
        "border": "#d5dfe8",
        "link": "#1570a6",
        "code_bg": "#eef4f8",
        "code_text": "#23384a",
        "quote_bg": "#eff7fb",
        "quote_border": "#1da1d2",
        "table_header": "#e6f0f7",
        "selection": "rgba(29, 161, 210, 0.16)",
        "body_font": '"Libre Baskerville", Georgia, serif',
        "heading_font": '"Playfair Display", "Libre Baskerville", serif',
        "article_padding": "36px 48px 52px",
        "article_radius": "26px",
        "article_border": "1px solid rgba(213, 223, 232, 0.96)",
        "article_shadow": "0 26px 56px rgba(21, 112, 166, 0.10)",
        "h1_color": "#102a43",
        "h2_color": "#1f4f73",
        "h1_letter_spacing": "0.04em",
        "h1_transform": "uppercase",
        "link_weight": "600",
        "link_underline": "none",
        "blockquote_radius": "18px",
        "code_border": "1px solid rgba(213, 223, 232, 0.96)",
        "table_radius": "16px",
    },
    "modest": {
        "page_bg": "#f3f3f1",
        "panel_bg": "#fffdf9",
        "text": "#242424",
        "muted": "#6d6d68",
        "border": "#d7d3ca",
        "link": "#394e6a",
        "code_bg": "#f0ece4",
        "code_text": "#2f2f2f",
        "quote_bg": "#f7f3ec",
        "quote_border": "#8f8a7d",
        "table_header": "#ece7de",
        "selection": "rgba(57, 78, 106, 0.14)",
        "body_font": '"Atkinson Hyperlegible", "Noto Sans", sans-serif',
        "heading_font": '"Atkinson Hyperlegible", "Noto Sans", sans-serif',
        "article_padding": "28px 32px 38px",
        "article_radius": "6px",
        "article_border": "1px solid rgba(215, 211, 202, 0.98)",
        "article_shadow": "none",
        "h1_color": "#202020",
        "h2_color": "#303030",
        "h1_letter_spacing": "0",
        "h1_transform": "none",
        "link_weight": "500",
        "link_underline": "underline",
        "blockquote_radius": "2px",
        "code_border": "1px solid rgba(215, 211, 202, 0.98)",
        "table_radius": "2px",
    },
    "retro": {
        "page_bg": "#efe0bd",
        "panel_bg": "#f7efd9",
        "text": "#5f4630",
        "muted": "#866b4a",
        "border": "#b99563",
        "link": "#8c5a13",
        "code_bg": "#eadbb6",
        "code_text": "#59493c",
        "quote_bg": "#f3e6c4",
        "quote_border": "#a56a1f",
        "table_header": "#e7d39e",
        "selection": "rgba(165, 106, 31, 0.16)",
        "body_font": '"Courier Prime", "Courier New", monospace',
        "heading_font": '"Special Elite", "Courier Prime", monospace',
        "article_padding": "30px 34px 42px",
        "article_radius": "0px",
        "article_border": "2px solid rgba(185, 149, 99, 0.95)",
        "article_shadow": "8px 8px 0 rgba(119, 85, 43, 0.22)",
        "h1_color": "#6b3f14",
        "h2_color": "#855220",
        "h1_letter_spacing": "0.05em",
        "h1_transform": "uppercase",
        "link_weight": "700",
        "link_underline": "underline",
        "blockquote_radius": "0px",
        "code_border": "1px dashed rgba(165, 106, 31, 0.75)",
        "table_radius": "0px",
    },
    "air": {
        "page_bg": "#f6fbfb",
        "panel_bg": "#feffff",
        "text": "#49646b",
        "muted": "#7e9aa0",
        "border": "#c7dde0",
        "link": "#207ba3",
        "code_bg": "#edf7f8",
        "code_text": "#49646b",
        "quote_bg": "#eef8f7",
        "quote_border": "#2aa198",
        "table_header": "#e8f4f5",
        "selection": "rgba(32, 123, 163, 0.14)",
        "body_font": '"Nunito Sans", "Noto Sans", sans-serif',
        "heading_font": '"Manrope", "Nunito Sans", sans-serif',
        "article_padding": "34px 44px 48px",
        "article_radius": "28px",
        "article_border": "1px solid rgba(199, 221, 224, 0.95)",
        "article_shadow": "0 24px 54px rgba(42, 161, 152, 0.10)",
        "h1_color": "#1f5d66",
        "h2_color": "#2e7280",
        "h1_letter_spacing": "-0.035em",
        "h1_transform": "none",
        "link_weight": "600",
        "link_underline": "none",
        "blockquote_radius": "20px",
        "code_border": "1px solid rgba(199, 221, 224, 0.95)",
        "table_radius": "18px",
    },
}


class HtmlPreviewService:
    @staticmethod
    def build_base_uri(current_file=None):
        base_dir = Path(os.path.dirname(current_file) if current_file else os.getcwd()).resolve()
        uri = base_dir.as_uri()
        return uri if uri.endswith("/") else f"{uri}/"

    @staticmethod
    def render_document(markdown_text, title="Markdown Document", render_style="default", max_width_chars=0):
        body = HtmlPreviewService.render_body(markdown_text)
        has_body = bool(body.strip())
        css = HtmlPreviewService.build_css(render_style, max_width_chars)
        return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <style>{css}</style>
  <script>
    window.__mdEditorGetScrollRatio = function () {{
      const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      return Math.min(1, Math.max(0, window.scrollY / max));
    }};
    window.__mdEditorSetScrollRatio = function (ratio) {{
      const normalized = Math.min(1, Math.max(0, Number(ratio) || 0));
      const max = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
      window.scrollTo({{ top: normalized * max, behavior: 'auto' }});
    }};
  </script>
</head>
<body>
  <main class="markdown-shell">
{article_open}
{body}
{article_close}
  </main>
</body>
</html>""".format(
            title=html.escape(title),
            css=css,
            article_open='    <article class="markdown-body">' if has_body else "",
            article_close='    </article>' if has_body else "",
            body=body,
        )

    @staticmethod
    def render_body(markdown_text):
        text = markdown_text or ""
        if not text.strip():
            return ""

        if MARKDOWN_IT_AVAILABLE:
            renderer = MarkdownIt(
                "gfm-like",
                {
                    "html": False,
                    "linkify": False,
                    "typographer": False,
                    "breaks": False,
                },
            )
            html_output = renderer.render(text)
        elif MARKDOWN_AVAILABLE:
            html_output = markdown.markdown(
                text,
                extensions=["tables", "fenced_code", "sane_lists"],
            )
        else:
            html_output = "<pre><code>{}</code></pre>".format(html.escape(text))

        return HtmlPreviewService._render_task_lists(html_output)

    @staticmethod
    def build_css(render_style="default", max_width_chars=0):
        theme = HTML_THEMES.get(render_style, HTML_THEMES["default"])
        max_width_rule = f"max-width: {max_width_chars}ch;" if max_width_chars else "max-width: 920px;"
        return f"""
:root {{
  color-scheme: {'dark' if render_style == 'nocturne' else 'light'};
  --page-bg: {theme['page_bg']};
  --panel-bg: {theme['panel_bg']};
  --text-color: {theme['text']};
  --muted-color: {theme['muted']};
  --border-color: {theme['border']};
  --link-color: {theme['link']};
  --code-bg: {theme['code_bg']};
  --code-color: {theme['code_text']};
  --quote-bg: {theme['quote_bg']};
  --quote-border: {theme['quote_border']};
  --table-header-bg: {theme['table_header']};
  --selection-bg: {theme['selection']};
  --body-font: {theme.get('body_font', '"Noto Sans", "DejaVu Sans", sans-serif')};
  --heading-font: {theme.get('heading_font', theme.get('body_font', '"Noto Sans", "DejaVu Sans", sans-serif'))};
  --article-padding: {theme.get('article_padding', '28px 34px 40px')};
  --article-radius: {theme.get('article_radius', '18px')};
  --article-border: {theme.get('article_border', f"1px solid {theme['border']}")};
  --article-shadow: {theme.get('article_shadow', '0 18px 42px rgba(15, 23, 42, 0.05)')};
  --h1-color: {theme.get('h1_color', theme['text'])};
  --h2-color: {theme.get('h2_color', theme['text'])};
  --h1-letter-spacing: {theme.get('h1_letter_spacing', '-0.03em')};
  --h1-transform: {theme.get('h1_transform', 'none')};
  --link-weight: {theme.get('link_weight', '600')};
  --link-underline: {theme.get('link_underline', 'none')};
  --blockquote-radius: {theme.get('blockquote_radius', '10px')};
  --code-border: {theme.get('code_border', f"1px solid {theme['border']}")};
  --table-radius: {theme.get('table_radius', '12px')};
}}
* {{
  box-sizing: border-box;
}}
html {{
  scroll-behavior: smooth;
}}
body {{
  margin: 0;
  background: var(--page-bg);
  color: var(--text-color);
  font-family: var(--body-font);
  font-size: 16px;
  line-height: 1.65;
}}
::selection {{
  background: var(--selection-bg);
}}
.markdown-shell {{
  padding: 24px;
}}
.markdown-body {{
  {max_width_rule}
  margin: 0 auto;
  padding: var(--article-padding);
  color: var(--text-color);
  background: var(--panel-bg);
  border: var(--article-border);
  border-radius: var(--article-radius);
  box-shadow: var(--article-shadow);
}}
.markdown-body > *:first-child {{
  margin-top: 0;
}}
.markdown-body > *:last-child {{
  margin-bottom: 0;
}}
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {{
  margin: 1.5em 0 0.6em;
  line-height: 1.25;
  color: var(--text-color);
  font-weight: 700;
  font-family: var(--heading-font);
}}
.markdown-body h1 {{
  font-size: 2em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--border-color);
  color: var(--h1-color);
  letter-spacing: var(--h1-letter-spacing);
  text-transform: var(--h1-transform);
}}
.markdown-body h2 {{
  font-size: 1.5em;
  padding-bottom: 0.25em;
  border-bottom: 1px solid var(--border-color);
  color: var(--h2-color);
}}
.markdown-body h3 {{
  font-size: 1.25em;
}}
.markdown-body h4 {{
  font-size: 1.05em;
}}
.markdown-body h5 {{
  font-size: 0.95em;
}}
.markdown-body h6 {{
  font-size: 0.9em;
  color: var(--muted-color);
}}
.markdown-body p,
.markdown-body ul,
.markdown-body ol,
.markdown-body blockquote,
.markdown-body table,
.markdown-body pre {{
  margin: 0 0 1rem;
}}
.markdown-body ul,
.markdown-body ol {{
  padding-left: 1.6rem;
}}
.markdown-body li + li {{
  margin-top: 0.25rem;
}}
.markdown-body a {{
  color: var(--link-color);
  text-decoration: var(--link-underline);
  font-weight: var(--link-weight);
  text-underline-offset: 0.14em;
}}
.markdown-body a:hover {{
  text-decoration: underline;
}}
.markdown-body strong {{
  font-weight: 700;
}}
.markdown-body hr {{
  border: 0;
  border-top: 1px solid var(--border-color);
  margin: 1.5rem 0;
}}
.markdown-body blockquote {{
  margin-left: 0;
  padding: 0.45rem 1rem;
  color: var(--muted-color);
  background: var(--quote-bg);
  border-left: 4px solid var(--quote-border);
  border-radius: var(--blockquote-radius);
}}
.markdown-body code {{
  font-family: "JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas", monospace;
  font-size: 0.9em;
  background: var(--code-bg);
  color: var(--code-color);
  border-radius: 6px;
  padding: 0.12em 0.35em;
}}
.markdown-body pre {{
  background: var(--code-bg);
  color: var(--code-color);
  border: var(--code-border);
  border-radius: 8px;
  padding: 1rem 1.1rem;
  overflow-x: auto;
}}
.markdown-body pre code {{
  background: transparent;
  border-radius: 0;
  padding: 0;
  font-size: 0.88em;
}}
.markdown-body table {{
  width: 100%;
  border-collapse: collapse;
  display: block;
  overflow-x: auto;
  border-radius: var(--table-radius);
}}
.markdown-body th,
.markdown-body td {{
  padding: 0.55rem 0.8rem;
  border: 1px solid var(--border-color);
  text-align: left;
  vertical-align: top;
}}
.markdown-body th {{
  background: var(--table-header-bg);
  font-weight: 700;
}}
.markdown-body img {{
  max-width: 100%;
  height: auto;
}}
.markdown-body .task-list {{
  list-style: none;
  padding-left: 0;
}}
.markdown-body .task-list .task-list {{
  margin-top: 0.25rem;
  padding-left: 1.5rem;
}}
.markdown-body .task-list-item {{
  display: flex;
  align-items: flex-start;
  gap: 0.55rem;
}}
.markdown-body .task-list-item input {{
  margin-top: 0.28rem;
}}
.markdown-body .task-list-item-checkbox {{
  accent-color: var(--link-color);
}}

@media print {{
  @page {{
    size: A4;
    margin: 10mm 9mm 12mm;
  }}

  html,
  body {{
    background: #ffffff;
  }}

  body {{
    font-size: 10.5px;
    line-height: 1.32;
    color: #111111;
  }}

  .markdown-shell {{
    padding: 0;
  }}

  .markdown-body {{
    max-width: none;
    padding: 0;
    border: 0;
    border-radius: 0;
    box-shadow: none;
    background: #ffffff;
  }}

  .markdown-body h1 {{
    font-size: 1.45em;
  }}

  .markdown-body h2 {{
    font-size: 1.2em;
  }}

  .markdown-body h3 {{
    font-size: 1.06em;
  }}

  .markdown-body h4,
  .markdown-body h5,
  .markdown-body h6 {{
    font-size: 1em;
  }}

  .markdown-body p,
  .markdown-body ul,
  .markdown-body ol,
  .markdown-body blockquote,
  .markdown-body table,
  .markdown-body pre {{
    margin: 0 0 0.45rem;
  }}

  .markdown-body ul,
  .markdown-body ol {{
    padding-left: 1rem;
  }}

  .markdown-body h1,
  .markdown-body h2,
  .markdown-body h3,
  .markdown-body h4,
  .markdown-body h5,
  .markdown-body h6 {{
    margin: 0.95em 0 0.35em;
  }}

  .markdown-body code {{
    font-size: 0.78em;
    padding: 0.04em 0.18em;
  }}

  .markdown-body pre {{
    padding: 0.45rem 0.55rem;
    border-radius: 3px;
  }}

  .markdown-body th,
  .markdown-body td {{
    padding: 0.2rem 0.3rem;
    font-size: 0.88em;
  }}

  .markdown-body blockquote {{
    padding: 0.18rem 0.5rem;
    border-left-width: 2px;
  }}

  .markdown-body img {{
    max-height: 140mm;
    page-break-inside: avoid;
  }}

  .markdown-body h1,
  .markdown-body h2,
  .markdown-body h3,
  .markdown-body h4,
  .markdown-body h5,
  .markdown-body h6,
  .markdown-body pre,
  .markdown-body table,
  .markdown-body blockquote,
  .markdown-body img {{
    break-inside: avoid;
  }}
}}
"""

    @staticmethod
    def _render_task_lists(html_output):
        def replace_list(match):
            list_tag = match.group("tag")
            content = match.group("content")

            replaced_content = re.sub(
                r"<li>\s*\[([ xX])\]\s*(.*?)</li>",
                HtmlPreviewService._build_task_item,
                content,
                flags=re.DOTALL,
            )

            if replaced_content == content:
                return match.group(0)

            return f'<{list_tag} class="task-list">{replaced_content}</{list_tag}>'

        return re.sub(
            r"<(?P<tag>ul|ol)>(?P<content>.*?)</(?P=tag)>",
            replace_list,
            html_output,
            flags=re.DOTALL,
        )

    @staticmethod
    def _build_task_item(match):
        checked = match.group(1).lower() == "x"
        content = match.group(2).strip()
        checked_attr = ' checked=""' if checked else ""
        return (
            '<li class="task-list-item">'
            f'<input class="task-list-item-checkbox" type="checkbox" disabled=""{checked_attr}>'
            f'<span>{content}</span>'
            "</li>"
        )
