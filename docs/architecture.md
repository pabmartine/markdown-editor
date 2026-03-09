# Architecture

The project is organized as a Python package under `src/markdown_editor`.

- `core/`: constants, configuration and internationalization.
- `models/`: shared document models.
- `repositories/`: persistence helpers for local config/state.
- `services/`: HTML preview generation, export, session recovery and document logic.
- `ui/`: GTK window, CSS styles and UI support mixins.
- `tests/`: non-GUI regression tests for parsing, rendering and editor logic.
- `main.py`: application entrypoint.
- `app.py`: `Adw.Application` setup, preferences and global actions.

## Runtime Flow

1. `main.py` starts the application.
2. `app.py` creates `MarkdownEditorWindow`.
3. `window.py` coordinates editor state, the embedded `WebKit` preview and view/layout changes.
4. `services/html_preview.py` converts Markdown to themed HTML and provides screen/print CSS.
5. `services/export_service.py` reuses the same HTML pipeline for export.
6. `app.py` routes print/PDF export through `WebKit.PrintOperation`, so printed output matches the preview.

## UI Organization

- Header bar: primary document actions and app menu.
- Toolbar: Markdown insertion actions and editor/preview view toggles.
- Main content: optional outline, editor pane and embedded HTML preview pane.
- Preferences: language, appearance, editor, preview style and recovery settings.
