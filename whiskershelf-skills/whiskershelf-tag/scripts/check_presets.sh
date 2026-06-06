#!/usr/bin/env bash
# check_presets.sh — bash wrapper
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/check_presets.py" "$@"
