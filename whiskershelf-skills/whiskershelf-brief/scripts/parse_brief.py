#!/usr/bin/env python3
"""
parse_brief.py — Parse a WhiskerShelf Idea Spark brief.md into structured data.

Usage:
    python parse_brief.py <brief.md>                # Human-readable summary
    python parse_brief.py <brief.md> --direction N  # Focus on N-th direction
    python parse_brief.py <brief.md> --json         # Machine-readable JSON
    python parse_brief.py <brief.md> --no-color     # Disable ANSI colors

Stdlib-only. No external dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Make stdout safe on Windows GBK terminals (we still try to be helpful
# with emoji/icons, but degrade gracefully when the codec refuses).
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

# Symbol sets — emoji used when stdout supports UTF-8, ASCII fallback otherwise.
_HAS_EMOJI = True
try:
    sys.stdout.write("")
    sys.stdout.flush()
    # Probe with a sample emoji to a temporary buffer to avoid leaking to real output.
    import io as _io
    _probe = _io.StringIO()
    _probe.write("✅")
    _probe.getvalue()  # this only fails at encode time, not write
except UnicodeEncodeError:
    _HAS_EMOJI = False

# A more reliable probe: try to encode the emoji with the current stdout's codec.
try:
    "✅".encode(sys.stdout.encoding or "utf-8")
except (UnicodeEncodeError, LookupError, AttributeError):
    _HAS_EMOJI = False


# Canonical field names as the Idea Spark LLM is prompted to produce.
# We match them with optional surrounding ** ** (bold markdown).
# Lookahead: stop at next bold field, next ### subheading, next ## section, or EOS.
FIELD_PATTERNS: dict[str, re.Pattern[str]] = {
    "core_idea": re.compile(r"\*\*核心\s*Idea\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
    "method_transfer": re.compile(r"\*\*方法迁移路径\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
    "expected_challenges": re.compile(r"\*\*预期难点\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
    "validation": re.compile(r"\*\*验证方案\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
    "cross_domain": re.compile(r"\*\*可能的跨域跳跃\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
}

# Loose English variants the LLM may fall back to under "thinking mode" or translation.
FIELD_PATTERNS_LOOSE: dict[str, re.Pattern[str]] = {
    "core_idea": re.compile(r"\*\*(?:Core\s*Idea|Idea|Pitch)\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
    "method_transfer": re.compile(r"\*\*(?:Method\s*Transfer|Approach|Transfer\s*Path)\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
    "expected_challenges": re.compile(r"\*\*(?:Expected\s*Challenges?|Challenges?|Risks?)\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
    "validation": re.compile(r"\*\*(?:Validation|Experiment|Verification)\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
    "cross_domain": re.compile(r"\*\*(?:Cross[-\s]*[Dd]omain|Adjacent|Leap)\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n##\s|\Z)", re.DOTALL),
}


def _strip(text: str) -> str:
    return text.strip().rstrip()


def parse_brief(text: str) -> dict[str, Any]:
    """Parse a brief.md string into a structured dict."""
    # Top-level metadata
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = _strip(title_match.group(1)) if title_match else ""

    papers_match = re.search(r"^>\s*选中论文:\s*(.+)$", text, re.MULTILINE)
    papers_line = _strip(papers_match.group(1)) if papers_match else ""

    context_match = re.search(r"^>\s*用户补充上下文:\s*(.+)$", text, re.MULTILINE)
    user_context = _strip(context_match.group(1)) if context_match else ""

    # Per-direction blocks. Match "### 方向 N: <title>" or "### Direction N:" etc.
    direction_header_re = re.compile(
        r"^###\s+(?:方向|Direction)\s*(\d+)\s*[:：]\s*(.+)$",
        re.MULTILINE,
    )
    # A direction block ends at the next ### subheading OR the next ## top-level section.
    # This prevents field regexes from bleeding into the cross-domain / risks / reasoning
    # sections when the last direction is the final block before those.
    block_end_re = re.compile(r"^#{2,3}\s", re.MULTILINE)

    headers = list(direction_header_re.finditer(text))
    directions: list[dict[str, Any]] = []
    missing_fields_total: list[str] = []

    for i, m in enumerate(headers):
        start = m.end()
        if i + 1 < len(headers):
            end = headers[i + 1].start()
        else:
            # Last direction: block ends at next ## or ### heading, not at EOF
            next_section = block_end_re.search(text, start)
            end = next_section.start() if next_section else len(text)
        block = text[start:end]

        d: dict[str, Any] = {
            "index": int(m.group(1)),
            "title": _strip(m.group(2)),
            "core_idea": None,
            "method_transfer": None,
            "expected_challenges": None,
            "validation": None,
            "cross_domain": None,
        }
        for key, pat in FIELD_PATTERNS.items():
            mm = pat.search(block)
            if mm:
                d[key] = _strip(mm.group(1))
        # Fall back to loose English patterns if Chinese ones missed.
        for key, pat in FIELD_PATTERNS_LOOSE.items():
            if d[key] is None:
                mm = pat.search(block)
                if mm:
                    d[key] = _strip(mm.group(1))

        missing = [k for k in ("core_idea", "method_transfer", "expected_challenges", "validation") if d[k] is None]
        d["missing_fields"] = missing
        missing_fields_total.extend(f"方向{d['index']}.{k}" for k in missing)
        directions.append(d)

    # Cross-domain section (after the last direction).
    cross_section = re.search(
        r"^##\s+(?:3\.\s*)?跨域跳跃建议\s*$\n(.*?)(?=^##|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    cross_section_text = _strip(cross_section.group(1)) if cross_section else ""

    # Risks section.
    risks_section = re.search(
        r"^##\s+(?:4\.\s*)?风险(?:与盲点)?\s*$\n(.*?)(?=^##|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    risks_text = _strip(risks_section.group(1)) if risks_section else ""

    # Reasoning block (optional, present when thinking mode was on).
    reasoning_match = re.search(
        r"^##\s+思考过程\s*$\n```[a-z]*\n(.*?)\n```",
        text,
        re.MULTILINE | re.DOTALL,
    )
    reasoning = _strip(reasoning_match.group(1)) if reasoning_match else None

    return {
        "title": title,
        "papers_line": papers_line,
        "user_context": user_context,
        "directions": directions,
        "cross_domain_section": cross_section_text,
        "risks_section": risks_text,
        "reasoning_present": reasoning is not None,
        "missing_fields_total": missing_fields_total,
    }


def _truncate(s: str | None, n: int) -> str:
    if s is None:
        return "(missing)"
    s = s.replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _icon(emoji: str, ascii_fallback: str) -> str:
    return emoji if _HAS_EMOJI else ascii_fallback


def print_human(parsed: dict[str, Any], focus: int | None, use_color: bool) -> None:
    def c(code: str, s: str) -> str:
        if not use_color:
            return s
        return f"\033[{code}m{s}\033[0m"

    print(c("1;36", f"{_icon('📄', '[brief]')} {parsed['title']}"))
    if parsed["papers_line"]:
        print(c("2", f"   选中论文: {parsed['papers_line']}"))
    if parsed["user_context"] and parsed["user_context"] != "无":
        print(c("2", f"   用户上下文: {parsed['user_context']}"))
    print()

    if parsed["missing_fields_total"]:
        warn = _icon("⚠️ ", "[warn] ") + "缺失字段: " + ", ".join(parsed["missing_fields_total"])
        print(c("33", warn))
        print()

    directions = parsed["directions"]
    if focus is not None:
        if focus < 0 or focus >= len(directions):
            print(c("31", f"--direction {focus} out of range (have {len(directions)} directions)"))
            sys.exit(2)
        directions = [directions[focus]]

    for d in directions:
        print(c("1;33", f"### 方向 {d['index']}: {d['title']}"))
        for label, key in (
            ("核心 Idea", "core_idea"),
            ("方法迁移路径", "method_transfer"),
            ("预期难点", "expected_challenges"),
            ("验证方案", "validation"),
            ("跨域跳跃", "cross_domain"),
        ):
            val = d[key]
            ok = _icon("✓", "[ok]") if val else _icon("✗", "[MISSING]")
            print(f"  {ok} {c('1', label)}: {_truncate(val, 200)}")
        print()

    if focus is None:
        if parsed["cross_domain_section"]:
            print(c("1;35", f"### 跨域跳跃建议"))
            print(_truncate(parsed["cross_domain_section"], 400))
            print()
        if parsed["risks_section"]:
            print(c("1;35", f"### 风险与盲点"))
            print(_truncate(parsed["risks_section"], 400))
            print()
        if parsed["reasoning_present"]:
            print(c("2", "(brief 含思考过程；如需查看请直接读 brief.md 的 `## 思考过程` 段)"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Parse a WhiskerShelf Idea Spark brief.md")
    ap.add_argument("path", type=Path, help="Path to brief.md")
    ap.add_argument("--direction", type=int, default=None, help="Focus on the N-th direction (0-indexed)")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    ap.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    args = ap.parse_args()

    if not args.path.exists():
        print(f"brief not found: {args.path}", file=sys.stderr)
        return 2
    text = args.path.read_text(encoding="utf-8")
    parsed = parse_brief(text)

    if args.json:
        json.dump(parsed, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    print_human(parsed, args.direction, use_color=not args.no_color and sys.stdout.isatty())
    return 0


if __name__ == "__main__":
    sys.exit(main())
