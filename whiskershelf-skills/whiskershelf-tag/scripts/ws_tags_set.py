#!/usr/bin/env python3
"""
ws_tags_set.py — WRITE a paper's tag list (REPLACES existing list).

!! GATED ENDPOINT !!
Always follow the gating workflow in SKILL.md before calling this script:
  READ → PROPOSE → CONFIRM → EXECUTE (this script) → CONFIRM-AFTER.

This script does NOT enforce gating. It will write whatever you pass.
The `--require-confirm` flag adds an extra in-script confirmation prompt
as a safety net, but the workflow's primary defense is the agent.

Usage:
    python ws_tags_set.py "Spikformer v2.pdf" --tags "脉冲神经网络 SNN,Transformer"
    python ws_tags_set.py "Spikformer v2.pdf" --tags "SNN,custom-tag" --require-confirm
    python ws_tags_set.py "Spikformer v2.pdf" --clear                  # remove all tags
    python ws_tags_set.py "Spikformer v2.pdf" --tags "SNN" --dry-run   # show what would happen
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import quote

from ws_common import DEFAULT_BASE, require_server, request


def main() -> int:
    ap = argparse.ArgumentParser(description="WRITE a paper's tag list (gated; use with care)")
    ap.add_argument("name", help="PDF filename")
    ap.add_argument("--tags", help="comma-separated new tag list (REPLACES existing)")
    ap.add_argument("--clear", action="store_true", help="remove all tags")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--require-confirm", action="store_true",
                    help="prompt on stdin for confirmation before writing")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the request that would be sent and exit")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.clear and args.tags:
        ap.error("--clear and --tags are mutually exclusive")
    if not args.clear and not args.tags:
        ap.error("either --tags <list> or --clear is required")

    require_server(args.base)
    name_quoted = quote(args.name, safe="")
    tags_path = f"/api/agent/papers/{name_quoted}/tags"

    # Read current tags so the user / dry-run can see the diff.
    try:
        current_resp = request("GET", tags_path, base=args.base)
        current = list(current_resp.get("tags") or [])
    except Exception as e:
        print(f"error reading current tags: {e}", file=sys.stderr)
        return 1

    if args.clear:
        new_tags: list[str] = []
    else:
        new_tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        # Server de-dupes; do the same here so the preview is faithful.
        seen: set[str] = set()
        deduped: list[str] = []
        for t in new_tags:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        new_tags = deduped

    added = [t for t in new_tags if t not in current]
    removed = [t for t in current if t not in new_tags]
    kept = [t for t in new_tags if t in current]

    print(f"Paper: {args.name}")
    print(f"  current ({len(current)}): {', '.join(current) or '(none)'}")
    print(f"  new     ({len(new_tags)}): {', '.join(new_tags) or '(none)'}")
    if added:
        print(f"  + add: {', '.join(added)}")
    if removed:
        print(f"  - del: {', '.join(removed)}")
    if kept:
        print(f"  = keep: {', '.join(kept)}")

    if args.dry_run:
        print("\n(dry-run: not writing)")
        return 0

    if args.require_confirm:
        print("\nType 'yes' to write, anything else to abort: ", end="", flush=True)
        try:
            ans = input()
        except EOFError:
            ans = ""
        if ans.strip().lower() != "yes":
            print("aborted.")
            return 0

    # Write
    try:
        resp = request("POST", tags_path, base=args.base, body={"tags": new_tags})
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    else:
        new = resp.get("tags") or []
        print(f"\n✓ wrote {len(new)} tag(s): {', '.join(new)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
