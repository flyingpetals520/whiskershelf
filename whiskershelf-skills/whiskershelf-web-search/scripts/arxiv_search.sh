#!/usr/bin/env bash
# arxiv_search.sh — bash wrapper
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/arxiv_search.py" "$@"
