#!/usr/bin/env python3
"""
check_presets.py — Verify candidate tags against the WhiskerShelf preset list.

This is a READ-ONLY helper. Use it during the PROPOSE step of the gating
workflow to flag any candidate that isn't a preset, so the user can decide
whether to add a custom tag or pick a preset instead.

Usage:
    python check_presets.py "脉冲神经网络 SNN"
    python check_presets.py "脉冲神经网络 SNN" "Transformer" "custom-tag"
    python check_presets.py --propose "SNN,brain-inspired,custom-tag"
    python check_presets.py --propose "SNN" --json
    python check_presets.py --list               # dump the full preset catalog
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable

from ws_common import DEFAULT_BASE, require_server, request


def fetch_presets(base: str) -> list[str]:
    resp = request("GET", "/api/presets", base=base)
    # /api/presets returns a bare list of strings (newer WhiskerShelf versions)
    # OR a {"presets": [...]} envelope (older versions). Handle both.
    if isinstance(resp, list):
        return [str(x) for x in resp]
    if isinstance(resp, dict):
        return [str(x) for x in (resp.get("presets") or [])]
    return []


def split_propose(arg: str) -> list[str]:
    # Accept comma- or semicolon-separated, with optional surrounding whitespace.
    out: list[str] = []
    for piece in arg.replace(";", ",").split(","):
        s = piece.strip()
        if s:
            out.append(s)
    return out


def diff(candidates: Iterable[str], presets: list[str]) -> dict[str, list[str]]:
    preset_set = {p.strip() for p in presets}
    in_preset: list[str] = []
    custom: list[str] = []
    for c in candidates:
        if c in preset_set:
            in_preset.append(c)
        else:
            custom.append(c)
    return {"in_preset": in_preset, "custom": custom}


def print_human(res: dict[str, list[str]], candidates: list[str], presets: list[str]) -> None:
    print(f"Checked {len(candidates)} candidate(s) against {len(presets)} preset(s):\n")
    if res["in_preset"]:
        print("[in_preset]")
        for t in res["in_preset"]:
            print(f"  + {t}")
    if res["custom"]:
        print("\n[NOT in preset — would create a new custom tag]")
        for t in res["custom"]:
            # Suggest close matches
            close = _closest(t, presets, k=3)
            print(f"  ! {t}")
            if close:
                print(f"      close: {', '.join(close)}")
    if not res["custom"] and not res["in_preset"]:
        print("(no candidates given)")


def _closest(target: str, options: list[str], k: int = 3) -> list[str]:
    """Cheap similarity: case-folded substring + Levenshtein-like via difflib."""
    import difflib
    norm_t = target.lower()
    scored = []
    for o in options:
        score = difflib.SequenceMatcher(None, norm_t, o.lower()).ratio()
        # Boost exact substring matches.
        if norm_t in o.lower() or o.lower() in norm_t:
            score = max(score, 0.95)
        scored.append((score, o))
    scored.sort(reverse=True)
    return [o for s, o in scored[:k] if s > 0.45]


def main() -> int:
    ap = argparse.ArgumentParser(description="Check tag candidates against presets")
    ap.add_argument("tags", nargs="*", help="candidate tags (positional)")
    ap.add_argument("--propose", help="comma-separated candidates (alternative to positional)")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--list", action="store_true", help="print the full preset catalog and exit")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    require_server(args.base)
    try:
        presets = fetch_presets(args.base)
    except Exception as e:
        print(f"error fetching presets: {e}", file=sys.stderr)
        return 1

    if args.list:
        if args.json:
            print(json.dumps({"presets": presets}, ensure_ascii=False, indent=2))
        else:
            for p in presets:
                print(f"- {p}")
        return 0

    if args.propose:
        candidates = split_propose(args.propose)
    else:
        candidates = list(args.tags)

    if not candidates:
        ap.error("provide candidate tags as positional args or via --propose")

    res = diff(candidates, presets)
    if args.json:
        print(json.dumps({"candidates": candidates, "presets_total": len(presets), **res},
                         ensure_ascii=False, indent=2))
    else:
        print_human(res, candidates, presets)
    return 0 if not res["custom"] else 1  # exit 1 if any custom tags were flagged


if __name__ == "__main__":
    sys.exit(main())
