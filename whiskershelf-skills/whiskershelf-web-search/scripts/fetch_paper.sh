#!/usr/bin/env bash
# fetch_paper.sh — bash wrapper
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/fetch_paper.py" "$@"
