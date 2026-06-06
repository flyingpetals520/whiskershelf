#!/usr/bin/env bash
# ws_papers.sh — bash wrapper around ws_papers.py
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/ws_papers.py" "$@"
