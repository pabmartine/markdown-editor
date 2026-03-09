#!/bin/bash

set -e

exec "$(dirname "$0")/packaging/flatpak/build-flatpak.sh" "$@"
