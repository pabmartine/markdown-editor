#!/bin/bash

set -e

exec "$(dirname "$0")/scripts/compile_translations.sh" "$@"
