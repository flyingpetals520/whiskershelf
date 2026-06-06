#!/usr/bin/env bash
# ws_detail.sh — bash wrapper around ws_detail.py
# Usage: ws_detail.sh "Spikformer v2.pdf"
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/ws_detail.py" "$@"
