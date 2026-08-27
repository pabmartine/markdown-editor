APP_ID = "com.pabmartine.MarkdownEditor"
APP_NAME = "Markdown Editor"
APP_DOMAIN = "markdown-editor"
APP_VERSION = "1.4.0"
APP_WEBSITE = "https://github.com/pabmartine/markdown-editor"

DEFAULT_CONFIG = {
    "window_width": 1000,
    "window_height": 700,
    "paned_position": 500,
    # Kept only so an existing config can be migrated: the window reads
    # "color_scheme" first and falls back to this boolean. "color_scheme"
    # is deliberately absent here so its absence is detectable.
    "dark_theme": False,
    "language": "auto",
    "render_style": "default",
    "recent_files": [],
    "editor_font_size": 10,
    "editor_content_width": 0,
    "focus_mode": False,
    "auto_save_interval": 10,
    "auto_restore_session": True,
    "last_session_dirty": False,
}

MAX_RECENT_FILES = 10
