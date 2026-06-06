#!/usr/bin/env bash
# s2_search.sh — bash wrapper
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/s2_search.py" "$@"
