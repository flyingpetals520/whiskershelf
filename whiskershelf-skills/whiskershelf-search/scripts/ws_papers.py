#!/usr/bin/env python3
"""
ws_papers.py — List every paper in the local WhiskerShelf library.

Usage:
    python ws_papers.py
    python ws_papers.py --tag "脉冲神经网络 SNN"   # filter by tag
    python ws_papers.py --json
    python ws_papers.py --name-only
"""
from __future__ import annotations

import argparse
import sys

from ws_common import DEFAULT_BASE, print_json, require_server, request


def main() -> int:
    ap = argparse.ArgumentParser(description="List all WhiskerShelf papers")
    ap.add_argument("--base", default=DEFAULT_BASE, help="WhiskerShelf base URL")
    ap.add_argument("--tag", help="filter to papers with this tag")
    ap.add_argument("--name-only", action="store_true", help="print only filenames (one per line)")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    require_server(args.base)
    try:
        resp = request("GET", "/api/agent/papers", base=args.base)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    papers = resp.get("papers") or []
    if args.tag:
        papers = [p for p in papers if args.tag in (p.get("tags") or [])]

    if args.json:
        print_json({"papers": papers})
        return 0

    if args.name_only:
        for p in papers:
            print(p.get("name"))
        return 0

    if not papers:
        print("(no papers found)")
        return 0
    print(f"{len(papers)} paper(s):")
    for p in papers:
        title = p.get("title") or p.get("name")
        tags = ", ".join(p.get("tags") or [])
        line = f"  - {title}  [{p.get('name')}]"
        if tags:
            line += f"  tags: {tags}"
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
