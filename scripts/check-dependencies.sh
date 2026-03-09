#!/bin/bash

set -e

python3 "$(dirname "$0")/../markdown-editor.py" --test >/dev/null
echo "Dependencies and basic runtime checks passed."
