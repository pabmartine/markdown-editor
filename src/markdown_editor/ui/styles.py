from gi.repository import Gdk, Gtk


CSS_DATA = """
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
    min-height: 28px;
    min-width: 28px;
    margin: 2px 3px;
    border-radius: 6px;
    transition: all 80ms ease-in-out;
    border: none;
    box-shadow: none;
    padding: 4px;
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

.header-preview-label {
    text-align: left;
}

.header-preview-label-h1 {
    font-size: 22px;
    font-weight: 700;
}

.header-preview-label-h2 {
    font-size: 19px;
    font-weight: 700;
}

.header-preview-label-h3 {
    font-size: 17px;
    font-weight: 600;
}

.header-preview-label-h4 {
    font-size: 15px;
    font-weight: 600;
}

.header-preview-label-h5 {
    font-size: 13px;
    font-weight: 500;
}

.header-preview-label-h6 {
    font-size: 12px;
    font-weight: 500;
    opacity: 0.85;
}

.view-btn-active {
    background-color: alpha(@accent_color, 0.2);
    color: @accent_color;
}

.group-separator {
    margin: 4px 4px;
    opacity: 0.5;
    min-width: 1px;
    min-height: 24px;
    background: alpha(@borders, 0.5);
}

.toolbar {
    background: transparent;
    border-top: none;
    box-shadow: none;
    padding: 4px 0px;
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
    line-height: 1.42;
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

.recent-file-btn {
    font-size: 12px;
    padding: 2px 6px;
}

.preview-card {
    border-radius: 10px;
    border: 1px solid alpha(@borders, 0.8);
    background: alpha(@headerbar_bg_color, 0.45);
    padding: 8px 10px;
}

.preview-code-block {
    margin: 4px 0;
}

.preview-code-language {
    font-family: monospace;
    font-size: 10px;
    opacity: 0.75;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.preview-code-text {
    font-family: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.32;
}

.preview-table-frame {
    margin: 4px 0;
    border: 1px solid alpha(@borders, 0.85);
    background: transparent;
    border-radius: 0;
    overflow: hidden;
}

.preview-table {
    border-spacing: 0;
}

.preview-table-cell {
    background: alpha(@window_bg_color, 0.85);
    padding: 6px 10px;
    border-right: 1px solid alpha(@borders, 0.75);
    border-bottom: 1px solid alpha(@borders, 0.75);
}

.preview-table-header {
    background: alpha(@accent_bg_color, 0.16);
    font-weight: 700;
}

.preview-table-row-even {
    background: alpha(@window_bg_color, 0.92);
}

.preview-table-row-odd {
    background: alpha(@headerbar_bg_color, 0.22);
}

.preview-blockquote {
    background: alpha(@accent_bg_color, 0.08);
}

.preview-blockquote-rail {
    background: alpha(@accent_bg_color, 0.8);
    border-radius: 999px;
}

.preview-blockquote-text {
    font-style: italic;
}

.preview-task-block checkbutton {
    margin-top: 2px;
}

.preview-list-block {
    padding-top: 2px;
    padding-bottom: 2px;
}

.preview-list-bullet {
    font-family: monospace;
    font-weight: 700;
    min-width: 24px;
}

.preview-image-block {
    margin: 4px 0 8px 0;
}

.outline-active {
    background: alpha(@accent_color, 0.14);
    color: @accent_color;
    border-radius: 6px;
}

.preview-rule {
    opacity: 0.7;
}
"""


PREVIEW_THEME_COLORS = {
    "default": {
        "card_bg": "rgba(244, 246, 248, 0.9)",
        "card_border": "rgba(180, 188, 196, 0.9)",
        "code_bg": "rgba(236, 240, 243, 0.95)",
        "table_header_bg": "rgba(87, 117, 144, 0.14)",
        "table_alt_bg": "rgba(236, 240, 243, 0.45)",
        "blockquote_bg": "rgba(87, 117, 144, 0.08)",
        "blockquote_rail": "#577590",
    },
    "slate": {
        "card_bg": "rgba(246, 247, 249, 1.0)",
        "card_border": "rgba(203, 210, 220, 0.96)",
        "code_bg": "rgba(237, 241, 245, 1.0)",
        "table_header_bg": "rgba(237, 241, 245, 1.0)",
        "table_alt_bg": "rgba(237, 241, 245, 0.72)",
        "blockquote_bg": "rgba(246, 247, 249, 1.0)",
        "blockquote_rail": "#98a2b3",
        "card_radius": "6px",
        "cell_bg": "rgba(250, 251, 252, 1.0)",
        "table_border": "#cbd2dc",
        "muted_text": "#667085",
        "code_padding": "16px",
        "table_radius": "6px",
        "blockquote_padding": "0px",
        "blockquote_border": "0px",
        "list_padding": "0px",
        "list_border": "0px",
        "list_bg": "transparent",
        "task_padding": "0px",
        "task_border": "0px",
        "task_bg": "transparent",
        "image_padding": "0px",
        "image_border": "0px",
        "image_bg": "transparent",
    },
    "ivory": {
        "card_bg": "rgba(255, 252, 245, 1.0)",
        "card_border": "rgba(227, 220, 205, 0.96)",
        "code_bg": "rgba(247, 241, 232, 1.0)",
        "table_header_bg": "rgba(245, 239, 228, 1.0)",
        "table_alt_bg": "rgba(245, 239, 228, 0.72)",
        "blockquote_bg": "rgba(255, 252, 245, 1.0)",
        "blockquote_rail": "#b08968",
        "card_radius": "6px",
        "cell_bg": "rgba(255, 253, 248, 1.0)",
        "table_border": "#e3dccd",
        "muted_text": "#7c6f64",
        "code_padding": "16px",
        "table_radius": "6px",
        "blockquote_padding": "0px",
        "blockquote_border": "0px",
        "list_padding": "0px",
        "list_border": "0px",
        "list_bg": "transparent",
        "task_padding": "0px",
        "task_border": "0px",
        "task_bg": "transparent",
        "image_padding": "0px",
        "image_border": "0px",
        "image_bg": "transparent",
    },
    "nocturne": {
        "card_bg": "rgba(17, 24, 39, 0.98)",
        "card_border": "rgba(36, 48, 66, 0.98)",
        "code_bg": "rgba(11, 18, 32, 1.0)",
        "table_header_bg": "rgba(125, 211, 252, 0.14)",
        "table_alt_bg": "rgba(36, 48, 66, 0.56)",
        "blockquote_bg": "rgba(125, 211, 252, 0.08)",
        "blockquote_rail": "#7dd3fc",
        "card_radius": "6px",
        "cell_bg": "rgba(15, 23, 42, 0.85)",
        "table_border": "#243042",
        "muted_text": "#94a3b8",
        "code_padding": "16px",
        "table_radius": "6px",
        "blockquote_padding": "0px",
        "blockquote_border": "0px",
        "list_padding": "0px",
        "list_border": "0px",
        "list_bg": "transparent",
        "task_padding": "0px",
        "task_border": "0px",
        "task_bg": "transparent",
        "image_padding": "0px",
        "image_border": "0px",
        "image_bg": "transparent",
    },
    "ember": {
        "card_bg": "rgba(255, 248, 241, 1.0)",
        "card_border": "rgba(231, 214, 196, 1.0)",
        "code_bg": "rgba(247, 237, 226, 1.0)",
        "table_header_bg": "rgba(249, 241, 232, 1.0)",
        "table_alt_bg": "rgba(249, 241, 232, 0.78)",
        "blockquote_bg": "rgba(255, 248, 241, 1.0)",
        "blockquote_rail": "#c97b63",
        "card_radius": "4px",
        "cell_bg": "rgba(255, 251, 246, 1.0)",
        "table_border": "#e7d6c4",
        "muted_text": "#8a6a5b",
        "code_padding": "12px",
        "table_radius": "4px",
        "blockquote_padding": "0px",
        "blockquote_border": "0px",
        "list_padding": "0px",
        "list_border": "0px",
        "list_bg": "transparent",
        "task_padding": "0px",
        "task_border": "0px",
        "task_bg": "transparent",
        "image_padding": "0px",
        "image_border": "0px",
        "image_bg": "transparent",
    },
    "splendor": {
        "card_bg": "rgba(250, 250, 250, 0.98)",
        "card_border": "rgba(210, 216, 222, 0.96)",
        "code_bg": "rgba(236, 240, 241, 1.0)",
        "table_header_bg": "rgba(52, 152, 219, 0.14)",
        "table_alt_bg": "rgba(52, 152, 219, 0.06)",
        "blockquote_bg": "rgba(52, 152, 219, 0.07)",
        "blockquote_rail": "#3498db",
    },
    "modest": {
        "card_bg": "rgba(249, 249, 249, 0.98)",
        "card_border": "rgba(210, 210, 210, 0.96)",
        "code_bg": "rgba(245, 245, 245, 1.0)",
        "table_header_bg": "rgba(51, 122, 183, 0.12)",
        "table_alt_bg": "rgba(51, 122, 183, 0.05)",
        "blockquote_bg": "rgba(51, 122, 183, 0.05)",
        "blockquote_rail": "#337ab7",
    },
    "retro": {
        "card_bg": "rgba(245, 240, 221, 0.98)",
        "card_border": "rgba(205, 170, 125, 0.96)",
        "code_bg": "rgba(238, 232, 213, 1.0)",
        "table_header_bg": "rgba(181, 137, 0, 0.16)",
        "table_alt_bg": "rgba(181, 137, 0, 0.07)",
        "blockquote_bg": "rgba(181, 137, 0, 0.08)",
        "blockquote_rail": "#b58900",
    },
    "air": {
        "card_bg": "rgba(253, 246, 227, 0.98)",
        "card_border": "rgba(210, 198, 168, 0.96)",
        "code_bg": "rgba(238, 232, 213, 1.0)",
        "table_header_bg": "rgba(38, 139, 210, 0.14)",
        "table_alt_bg": "rgba(38, 139, 210, 0.06)",
        "blockquote_bg": "rgba(42, 161, 152, 0.08)",
        "blockquote_rail": "#2aa198",
    },
}


def build_theme_css(render_style):
    theme = PREVIEW_THEME_COLORS.get(render_style, PREVIEW_THEME_COLORS["default"])
    card_radius = theme.get("card_radius", "10px")
    cell_bg = theme.get("cell_bg", "rgba(255, 255, 255, 0.85)")
    table_border = theme.get("table_border", theme["card_border"])
    table_alt_bg = theme.get("table_alt_bg", theme["table_header_bg"])
    muted_text = theme.get("muted_text", theme["blockquote_rail"])
    code_padding = theme.get("code_padding", "10px 12px")
    table_radius = theme.get("table_radius", card_radius)
    blockquote_padding = theme.get("blockquote_padding", "10px 12px")
    blockquote_border = theme.get("blockquote_border", f'1px solid {theme["card_border"]}')
    list_padding = theme.get("list_padding", "10px 12px")
    list_border = theme.get("list_border", f'1px solid {theme["card_border"]}')
    list_bg = theme.get("list_bg", theme["card_bg"])
    task_padding = theme.get("task_padding", "10px 12px")
    task_border = theme.get("task_border", f'1px solid {theme["card_border"]}')
    task_bg = theme.get("task_bg", theme["card_bg"])
    image_padding = theme.get("image_padding", "0px")
    image_border = theme.get("image_border", "0px")
    image_bg = theme.get("image_bg", "transparent")
    return f"""
.preview-card {{
    border-color: {theme["card_border"]};
    background: {theme["card_bg"]};
    border-radius: {card_radius};
}}

.preview-code-block {{
    background: {theme["code_bg"]};
    padding: {code_padding};
}}

.preview-table-frame {{
    border-radius: 0;
    border: 1px solid {table_border};
    background: transparent;
}}

.preview-table-header,
.preview-list-bullet {{
    color: {theme["blockquote_rail"]};
}}

.preview-table-header {{
    background: {theme["table_header_bg"]};
    border-bottom: 1px solid {table_border};
}}

.preview-blockquote {{
    background: {theme["blockquote_bg"]};
    padding: {blockquote_padding};
    border: {blockquote_border};
}}

.preview-blockquote-rail {{
    background: {theme["blockquote_rail"]};
}}

.preview-list-block {{
    background: {list_bg};
    padding: {list_padding};
    border: {list_border};
}}

.preview-task-block {{
    background: {task_bg};
    padding: {task_padding};
    border: {task_border};
}}

.preview-image-block {{
    background: {image_bg};
    padding: {image_padding};
    border: {image_border};
}}

.preview-table-cell {{
    background: {cell_bg};
    border-right: 1px solid {table_border};
    border-bottom: 1px solid {table_border};
    padding: 8px 12px;
}}

.preview-table-row-even {{
    background: {cell_bg};
}}

.preview-table-row-odd {{
    background: {table_alt_bg};
}}

.preview-code-language,
.preview-blockquote-text,
.preview-rule {{
    color: {muted_text};
}}
"""


def apply_custom_css(render_style="default"):
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data((CSS_DATA + build_theme_css(render_style)).encode())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
