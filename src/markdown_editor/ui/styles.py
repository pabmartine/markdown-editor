from gi.repository import Gdk, Gtk


# Kept so a re-apply can replace it instead of stacking providers.
_provider = None


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
}

textview.editor-custom {
    font-family: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', 'Consolas', monospace;
    line-height: 1.5;
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

.outline-active {
    background: alpha(@accent_color, 0.14);
    color: @accent_color;
    border-radius: 6px;
}
"""


def apply_custom_css():
    """Install the app stylesheet, replacing any provider from a previous call.

    The previous version added a new provider on every invocation (and it is
    called again on each render-style change), so providers accumulated.
    """
    global _provider
    display = Gdk.Display.get_default()
    if display is None:
        return

    if _provider is not None:
        Gtk.StyleContext.remove_provider_for_display(display, _provider)

    _provider = Gtk.CssProvider()
    _provider.load_from_string(CSS_DATA)
    Gtk.StyleContext.add_provider_for_display(
        display,
        _provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
