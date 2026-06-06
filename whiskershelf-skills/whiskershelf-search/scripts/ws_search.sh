#!/usr/bin/env bash
# ws_search.sh — bash wrapper around ws_search.py
# Usage: ws_search.sh "spiking neural network"
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/ws_search.py" "$@"
