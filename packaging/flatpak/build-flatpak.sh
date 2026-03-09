#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_ID="com.pabmartine.MarkdownEditor"
BUILD_DIR="$REPO_ROOT/build-dir"
REPO_DIR="$REPO_ROOT/repo"
MANIFEST="$SCRIPT_DIR/$APP_ID.yaml"

echo "Preparando construcción de Flatpak..."
rm -rf "$BUILD_DIR" "$REPO_DIR"

echo "Verificando runtimes de Flatpak..."
if ! flatpak list --runtime | grep -q "org.gnome.Platform.*48"; then
    echo "Instalando runtime de GNOME Platform 48..."
    flatpak install --user flathub org.gnome.Platform//48 org.gnome.Sdk//48 -y
fi

echo "Compilando traducciones..."
"$REPO_ROOT/scripts/compile_translations.sh"

echo "Construyendo Flatpak..."
flatpak-builder --user --install --force-clean "$BUILD_DIR" "$MANIFEST"

echo "Creando repositorio local..."
flatpak-builder --user --repo="$REPO_DIR" --force-clean "$BUILD_DIR" "$MANIFEST"

echo "Creando bundle..."
flatpak build-bundle "$REPO_DIR" "$REPO_ROOT/$APP_ID.flatpak" "$APP_ID"

echo "Flatpak construido exitosamente."
echo
echo "Bundle generado:"
echo "  $REPO_ROOT/$APP_ID.flatpak"
echo
echo "Comandos útiles:"
echo "  Instalar el bundle:"
echo "    flatpak install --user \"$REPO_ROOT/$APP_ID.flatpak\""
echo
echo "  Ejecutar la app instalada:"
echo "    flatpak run $APP_ID"
echo
echo "  Ejecutar directamente desde el repositorio local generado:"
echo "    flatpak run --user --sideload-repo=\"$REPO_DIR\" $APP_ID"
