#!/usr/bin/env bash
# ws_tags_get.sh — bash wrapper
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/ws_tags_get.py" "$@"
