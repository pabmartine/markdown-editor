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

# La version se lee del manifiesto: estaba fijada a 48 mientras el manifiesto
# declaraba otra, asi que la comprobacion pasaba sin tener el runtime correcto.
RUNTIME_VERSION="$(sed -n "s/^runtime-version:[[:space:]]*['\"]\{0,1\}\([^'\"]*\)['\"]\{0,1\}[[:space:]]*$/\1/p" "$MANIFEST")"

echo "Verificando runtimes de Flatpak (version $RUNTIME_VERSION)..."
for rt in org.gnome.Platform org.gnome.Sdk; do
    if ! flatpak info "$rt//$RUNTIME_VERSION" >/dev/null 2>&1; then
        echo "Instalando $rt//$RUNTIME_VERSION..."
        flatpak install --user flathub "$rt//$RUNTIME_VERSION" -y
    fi
done

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
