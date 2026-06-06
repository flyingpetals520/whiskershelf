#!/usr/bin/env python3
"""
dispatch_pipeline.py — Build a 5-stage subagent dispatch plan for a brief direction.

This is a PLANNING helper. It never spawns anything — you still call the
`Task` tool yourself. The output is a checklist + ready-to-paste prompts.

Stdlib-only. Reads brief.md, parses it via the whiskershelf-brief parser
(imported from the sibling skill if available, else a tiny local fallback),
and prints a structured dispatch plan.

Usage:
    python dispatch_pipeline.py brief.md
    python dispatch_pipeline.py brief.md --direction 0
    python dispatch_pipeline.py brief.md --direction 0 --no-risk    # skip Stage 2B
    python dispatch_pipeline.py brief.md --direction 0 --max-papers 2
    python dispatch_pipeline.py brief.md --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SIBLING = Path(__file__).resolve().parent.parent.parent / "whiskershelf-brief" / "scripts"


def _load_brief_parser():
    """Try to import the brief parser from the sibling skill; fall back to a tiny local copy."""
    if (SIBLING / "parse_brief.py").exists():
        sys.path.insert(0, str(SIBLING))
        try:
            from parse_brief import parse_brief  # type: ignore
            return parse_brief
        except Exception:
            pass
    return _fallback_parse


def _fallback_parse(text: str) -> dict[str, Any]:
    """Minimal brief parser — duplicates only the bits dispatch_pipeline needs."""
    directions: list[dict[str, Any]] = []
    for m in re.finditer(r"^###\s+(?:方向|Direction)\s*(\d+)\s*[:：]\s*(.+)$", text, re.MULTILINE):
        directions.append({"index": int(m.group(1)), "title": m.group(2).strip()})
    return {"directions": directions, "title": ""}


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "references"


def _prompt(name: str, **subs: str) -> str:
    """Load a template from references/prompts/ and substitute placeholders."""
    p = PROMPTS_DIR / f"{name}.md"
    if not p.exists():
        return f"<<template {name} not found at {p}>>"
    text = p.read_text(encoding="utf-8")
    for k, v in subs.items():
        text = text.replace(f"<{k}>", v)
    return text


def build_plan(brief_path: Path, direction: int, *, include_risk: bool, max_papers: int) -> dict[str, Any]:
    parse_brief = _load_brief_parser()
    parsed = parse_brief(brief_path.read_text(encoding="utf-8"))
    directions = parsed.get("directions") or []
    if not directions:
        return {"error": "no directions found in brief.md"}
    if direction < 0 or direction >= len(directions):
        return {"error": f"--direction {direction} out of range (have {len(directions)})"}
    chosen = directions[direction]

    # Read selected-papers.json if present.
    papers: list[str] = []
    sp_path = brief_path.parent / "selected-papers.json"
    if sp_path.exists():
        try:
            data = json.loads(sp_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                papers = [p.get("name") for p in data if isinstance(p, dict) and p.get("name")]
        except Exception:
            pass

    # Build the dispatch list.
    dispatches: list[dict[str, str]] = []

    # Stage 1: one per paper (capped at max_papers)
    for name in papers[:max_papers]:
        dispatches.append({
            "stage": "1",
            "role": "per-paper",
            "paper": name,
            "purpose": f"Deep dive on {name}",
        })

    # Stage 2
    dispatches.append({
        "stage": "2A",
        "role": "method-transfer",
        "purpose": f"Design transfer pipeline for direction {chosen['index']}: {chosen.get('title', '')}",
    })
    if include_risk:
        dispatches.append({
            "stage": "2B",
            "role": "risk",
            "purpose": f"Attack the direction; surface failure modes",
        })
    dispatches.append({
        "stage": "2C",
        "role": "adjacent",
        "purpose": f"Find side doors / adjacent opportunities",
    })

    # Stage 3
    dispatches.append({
        "stage": "3",
        "role": "external-validation",
        "purpose": "Check arxiv + S2 for prior art; return GREEN/YELLOW/RED verdict",
    })

    return {
        "brief": str(brief_path),
        "direction_index": direction,
        "direction": chosen,
        "papers": papers[:max_papers],
        "dispatches": dispatches,
        "synthesis_template": "See references/dispatch-patterns.md → 'Pattern: I want a complete plan'",
    }


def print_human(plan: dict[str, Any]) -> None:
    if "error" in plan:
        print(f"error: {plan['error']}")
        return
    d = plan["direction"]
    print(f"# Dispatch Plan for Direction {plan['direction_index']}: {d.get('title', '')}\n")
    print(f"Brief: {plan['brief']}")
    if plan["papers"]:
        print(f"Papers ({len(plan['papers'])}):")
        for p in plan["papers"]:
            print(f"  - {p}")
    print()

    print(f"Total subagents to dispatch in one parallel batch: {len(plan['dispatches'])}\n")
    for i, dp in enumerate(plan["dispatches"], 1):
        print(f"[{i}] Stage {dp['stage']} — {dp['role']}")
        print(f"    purpose: {dp['purpose']}")
        if dp.get("paper"):
            print(f"    paper:   {dp['paper']}")
        print()

    print("→ All dispatches go in a SINGLE message (one batch, parallel).")
    print("→ After they return, you (the lead) synthesize the plan using the template at:")
    print(f"    {plan['synthesis_template']}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan a subagent dispatch for a brief direction")
    ap.add_argument("brief", type=Path, help="path to brief.md")
    ap.add_argument("--direction", type=int, default=0, help="direction index (0-based)")
    ap.add_argument("--max-papers", type=int, default=4, help="cap papers for Stage 1 (max 4)")
    ap.add_argument("--no-risk", action="store_true", help="skip Stage 2B (risk subagent)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.brief.exists():
        print(f"brief not found: {args.brief}", file=sys.stderr)
        return 2
    plan = build_plan(args.brief, args.direction,
                      include_risk=not args.no_risk,
                      max_papers=args.max_papers)
    if args.json:
        json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print_human(plan)
    return 0 if "error" not in plan else 1


if __name__ == "__main__":
    sys.exit(main())
