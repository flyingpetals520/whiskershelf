#!/usr/bin/env python3
"""
ws_detail.py — Fetch a single paper's full record (abstract, tags, notes).

Usage:
    python ws_detail.py "Spikformer v2.pdf"
    python ws_detail.py "脉冲神经网络综述.pdf" --json
    python ws_detail.py "Foo.pdf" --tags-only
    python ws_detail.py "Foo.pdf" --notes-only
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import quote

from ws_common import DEFAULT_BASE, print_json, require_server, request


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch one WhiskerShelf paper")
    ap.add_argument("name", help="PDF filename (URL-encoded automatically)")
    ap.add_argument("--base", default=DEFAULT_BASE, help="WhiskerShelf base URL")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    ap.add_argument("--tags-only", action="store_true", help="print only the tags")
    ap.add_argument("--notes-only", action="store_true", help="print only the notes")
    args = ap.parse_args()

    require_server(args.base)
    path = f"/api/agent/papers/{quote(args.name, safe='')}"
    try:
        paper = request("GET", path, base=args.base)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print_json(paper)
        return 0

    if args.tags_only:
        print(json.dumps(paper.get("tags", []), ensure_ascii=False))
        return 0
    if args.notes_only:
        print(paper.get("notes") or "")
        return 0

    print(f"# {paper.get('title') or paper.get('name')}")
    print(f"file: {paper.get('name')}")
    print(f"tags: {', '.join(paper.get('tags') or []) or '(none)'}")
    print()
    print("## Abstract")
    print((paper.get("abstract") or "(no abstract)").strip())
    print()
    print("## Notes")
    print((paper.get("notes") or "").strip() or "(no notes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
