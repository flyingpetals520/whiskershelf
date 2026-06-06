#!/usr/bin/env python3
"""
ws_tags_get.py — Read a paper's current tag list.

Usage:
    python ws_tags_get.py "Spikformer v2.pdf"
    python ws_tags_get.py "脉冲神经网络综述.pdf" --json
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import quote

from ws_common import DEFAULT_BASE, require_server, request


def main() -> int:
    ap = argparse.ArgumentParser(description="Read a paper's tags")
    ap.add_argument("name", help="PDF filename")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    require_server(args.base)
    path = f"/api/agent/papers/{quote(args.name, safe='')}/tags"
    try:
        resp = request("GET", path, base=args.base)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    tags = resp.get("tags") or []
    if args.json:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return 0
    if not tags:
        print("(no tags)")
    else:
        for t in tags:
            print(f"- {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
