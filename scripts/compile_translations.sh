#!/bin/bash

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Compilando archivos de traducción..."

for lang in en es; do
    if [ -f "$REPO_ROOT/locale/$lang/LC_MESSAGES/markdown-editor.po" ]; then
        msgfmt "$REPO_ROOT/locale/$lang/LC_MESSAGES/markdown-editor.po" \
               -o "$REPO_ROOT/locale/$lang/LC_MESSAGES/markdown-editor.mo"
        echo "Traducción compilada para: $lang"
    else
        echo "Archivo .po no encontrado para idioma: $lang"
    fi
done

echo "Compilación completada."
