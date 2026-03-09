# Packaging

Flatpak assets live in `packaging/flatpak/`.

- Manifest: `packaging/flatpak/com.pabmartine.MarkdownEditor.yaml`
- Helper script: `packaging/flatpak/build-flatpak.sh`

Convenience wrappers are still available at the repository root for compatibility.

## Notes

- The application now depends on an embedded `WebKit` preview for GTK4.
- Source builds therefore need the GTK4-compatible WebKitGTK introspection package, not just the shared library.
- Source builds also need `markdown-it-py` available to the Python interpreter used to launch the app.
- HTML export, PDF export and print all reuse the same themed HTML rendering pipeline.
