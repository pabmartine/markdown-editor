"""Icon names, with explicit fallbacks.

Thirteen of the names this app uses are provided by common desktop icon themes
but are *not* part of Adwaita, and the Flatpak runtime ships only Adwaita plus
hicolor. They render fine wherever the host theme supplies them (Flatpak
exposes host icon themes), but on a system that only has Adwaita the whole
formatting toolbar would come up as broken-image placeholders.

Each entry keeps the original name first, so the app looks exactly as before
where that name exists, followed by an Adwaita name to fall back to.
Resolution asks the icon theme directly rather than going through
Gio.ThemedIcon, whose multi-name lookup weighs available sizes and does not
reliably honour the given order.
"""

from gi.repository import Gdk, Gtk


ICON_NAMES = {
    # --- formatting toolbar ---------------------------------------------
    "bold": ["format-text-bold-symbolic"],
    "italic": ["format-text-italic-symbolic"],
    "strikethrough": ["format-text-strikethrough-fr-symbolic",
                      "format-text-strikethrough-symbolic"],
    "heading": ["font-size-symbolic", "font-select-symbolic"],
    "list-bullet": ["view-list-bullet-symbolic"],
    "list-ordered": ["format-ordered-list-symbolic", "view-list-ordered-symbolic"],
    "list-task": ["view-list-details-symbolic", "view-list-symbolic"],
    "quote": ["format-text-blockquote-symbolic", "chat-message-new-symbolic"],
    "code-inline": ["format-text-code-symbolic", "application-rss+xml-symbolic"],
    "code-block": ["code-context-symbolic", "utilities-terminal-symbolic"],
    "link": ["insert-link-symbolic"],
    "image": ["folder-images-symbolic", "insert-image-symbolic"],
    "table": ["folder-table-symbolic", "insert-object-symbolic"],
    "rule": ["menu_new_sep-symbolic", "list-remove-symbolic"],
    # --- view switcher ---------------------------------------------------
    "view-editor": ["document-edit-symbolic"],
    "view-split": ["text-frame-unlink-symbolic", "view-dual-symbolic"],
    "view-preview": ["multimedia-photo-viewer-symbolic", "view-reveal-symbolic"],
    # --- header bar and elsewhere ----------------------------------------
    "new": ["document-new-symbolic"],
    "open": ["document-open-symbolic"],
    "save": ["document-save-symbolic"],
    "search": ["system-search-symbolic"],
    "menu": ["open-menu-symbolic"],
    "up": ["go-up-symbolic"],
    "down": ["go-down-symbolic"],
    # "text-markdown-symbolic" exists in no icon theme; GTK was silently
    # falling back to the full-colour text-markdown mime icon.
    "markdown": ["text-markdown-symbolic", "text-x-generic-symbolic"],
}

_resolved = {}


def name(key):
    """First name in the chain that the current icon theme actually provides."""
    if key in _resolved:
        return _resolved[key]

    candidates = ICON_NAMES[key]
    chosen = candidates[-1]

    display = Gdk.Display.get_default()
    if display is not None:
        theme = Gtk.IconTheme.get_for_display(display)
        for candidate in candidates:
            if theme.has_icon(candidate):
                chosen = candidate
                break
        _resolved[key] = chosen

    return chosen

