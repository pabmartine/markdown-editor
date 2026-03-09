# Development

Useful commands:

```bash
python3 -m py_compile markdown-editor.py src/markdown_editor/*.py src/markdown_editor/core/*.py src/markdown_editor/services/*.py src/markdown_editor/ui/*.py
python3 -m unittest discover -s tests
python3 markdown-editor.py --test
```

The GTK application is launched through `markdown-editor.py`, which delegates to `markdown_editor.main`.

## Runtime Dependencies

For local development, install these required dependencies:

- GTK4 and libadwaita bindings
- WebKitGTK for GTK4 (`gir1.2-webkit-6.0` on Debian/Ubuntu)
- `markdown-it-py` for Markdown to HTML conversion

Recommended optional packages:

- `pygments`
- `python-markdown`

If WebKitGTK is missing, the application can still start but the preview pane cannot render the embedded HTML view.
