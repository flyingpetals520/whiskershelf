#!/usr/bin/env bash
# ws_tags_set.sh — bash wrapper for the GATED write.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/ws_tags_set.py" "$@"
