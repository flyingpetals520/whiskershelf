#!/usr/bin/env python3
"""
ws_search.py — Substring search the local WhiskerShelf library.

Usage:
    python ws_search.py "spiking neural network"
    python ws_search.py "spiking neural network" --json
    python ws_search.py "脉冲" --limit 5
"""
from __future__ import annotations

import argparse
import sys
from urllib.parse import quote

from ws_common import DEFAULT_BASE, print_json, require_server, request


def main() -> int:
    ap = argparse.ArgumentParser(description="WhiskerShelf local search")
    ap.add_argument("query", help="search term (substring, case-insensitive)")
    ap.add_argument("--base", default=DEFAULT_BASE, help="WhiskerShelf base URL")
    ap.add_argument("--limit", type=int, default=20, help="truncate results (server caps at 20)")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    require_server(args.base)
    try:
        resp = request("POST", "/api/agent/search", base=args.base, body={"query": args.query})
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    results = (resp.get("results") or [])[: args.limit]
    if args.json:
        print_json({"results": results})
        return 0

    if not results:
        print(f"(no results for '{args.query}')")
        return 0
    print(f"{len(results)} result(s) for '{args.query}':")
    for r in results:
        title = r.get("title") or r.get("name")
        preview = (r.get("abstract_preview") or "").replace("\n", " ").strip()
        print(f"  - {title}")
        if preview:
            print(f"      {preview[:120]}{'…' if len(preview) > 120 else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
