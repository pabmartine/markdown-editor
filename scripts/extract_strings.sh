#!/bin/bash
# Regenerates locale/markdown-editor.pot from the sources and merges it into
# every catalogue. Without this, strings added to the code never reached the
# catalogues and showed up untranslated at runtime.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOMAIN="markdown-editor"
POT="$ROOT_DIR/locale/$DOMAIN.pot"
VERSION="$(sed -n 's/^APP_VERSION = "\(.*\)"$/\1/p' "$ROOT_DIR/src/markdown_editor/core/constants.py")"

TEMP_FILE="$(mktemp)"
trap 'rm -f "$TEMP_FILE"' EXIT
find "$ROOT_DIR/src/markdown_editor" -name "*.py" | sort > "$TEMP_FILE"

xgettext --language=Python \
         --keyword=_ \
         --keyword=ngettext:1,2 \
         --output="$POT" \
         --from-code=UTF-8 \
         --add-comments \
         --copyright-holder="pabmartine" \
         --package-name="Markdown Editor" \
         --package-version="$VERSION" \
         --files-from="$TEMP_FILE"

echo "Generado $POT"

for lang in en es; do
    PO="$ROOT_DIR/locale/$lang/LC_MESSAGES/$DOMAIN.po"
    mkdir -p "$(dirname "$PO")"
    if [ -f "$PO" ]; then
        msgmerge --backup=none --no-fuzzy-matching --update "$PO" "$POT"
        echo "Actualizado $PO"
    else
        msginit --input="$POT" --output-file="$PO" --locale="$lang" --no-translator
        echo "Creado $PO"
    fi
done

echo "Listo. Revisa los .po y ejecuta scripts/compile_translations.sh"
