#!/usr/bin/env python3
"""
arxiv_search.py — Search arxiv.org for papers and return structured results.

Stdlib-only. Uses the public arxiv API (no key required):
    http://export.arxiv.org/api/query

Usage:
    python arxiv_search.py --query "spiking neural network associative memory"
    python arxiv_search.py --query "RWKV" --max 5 --since 2024
    python arxiv_search.py --query "spike-driven transformer" --cat cs.NE --json

The output is a table by default; use --json for machine-readable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any


ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom",
      "arxiv": "http://arxiv.org/schemas/atom"}


def search(query: str, *, max_results: int = 10, since_year: int | None = None,
           categories: list[str] | None = None, sort_by: str = "relevance") -> list[dict[str, Any]]:
    """Issue an arxiv search and return parsed entries."""
    q = query
    if categories:
        # Join with AND: (cat:cs.LG OR cat:cs.NE) becomes
        # cat:cs.LG OR cat:cs.NE   (arxiv API is OR within field, AND across)
        cat_clause = " OR ".join(f"cat:{c}" for c in categories)
        q = f"({q}) AND ({cat_clause})"
    if since_year:
        # submittedDate:[YYYY01010000 TO 209912312359]  (anything since the year)
        q = f"({q}) AND submittedDate:[{since_year}01010000 TO 209912312359]"

    params = {
        "search_query": q,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    }
    url = ARXIV_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "whiskershelf-web-search/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except Exception as e:
        print(f"arxiv request failed: {e}", file=sys.stderr)
        return []

    return _parse_atom(raw)


def _parse_atom(raw: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(raw)
    out: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", NS):
        title_el = entry.find("atom:title", NS)
        summary_el = entry.find("atom:summary", NS)
        id_el = entry.find("atom:id", NS)
        published_el = entry.find("atom:published", NS)
        updated_el = entry.find("atom:updated", NS)
        authors = [
            (a.find("atom:name", NS).text or "").strip()
            for a in entry.findall("atom:author", NS)
            if a.find("atom:name", NS) is not None
        ]
        cats = [
            (c.attrib.get("term") or "").strip()
            for c in entry.findall("atom:category", NS)
        ]
        link_pdf = ""
        for l in entry.findall("atom:link", NS):
            if l.attrib.get("title") == "pdf":
                link_pdf = l.attrib.get("href", "")
                break

        arxiv_id = ""
        if id_el is not None and id_el.text:
            m = re.search(r"abs/([^v]+)(v\d+)?$", id_el.text)
            arxiv_id = m.group(1) if m else id_el.text.strip()

        title = _whitespace(title_el.text) if title_el is not None and title_el.text else ""
        summary = _whitespace(summary_el.text) if summary_el is not None and summary_el.text else ""
        published = published_el.text.strip() if published_el is not None and published_el.text else ""

        # arxiv primary category is sometimes in arxiv:primary_category
        primary_el = entry.find("arxiv:primary_category", NS)
        primary = primary_el.attrib.get("term", "") if primary_el is not None else ""

        out.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "summary": summary,
            "published": published,
            "year": published[:4] if published else "",
            "categories": cats,
            "primary_category": primary,
            "url": (id_el.text or "").strip() if id_el is not None and id_el.text else "",
            "pdf_url": link_pdf,
        })
    return out


def _whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def print_human(results: list[dict[str, Any]], query: str) -> None:
    if not results:
        print(f"(no arxiv results for '{query}')")
        return
    print(f"{len(results)} arxiv result(s) for '{query}':\n")
    for r in results:
        print(f"[{r['arxiv_id']}] {r['title']}")
        print(f"  {', '.join(r['authors'][:3])}{'…' if len(r['authors']) > 3 else ''}  ({r['year']})")
        if r.get("primary_category"):
            print(f"  primary: {r['primary_category']}  | all: {', '.join(r['categories'])}")
        one_line = (r["summary"] or "").replace("\n", " ")
        print(f"  {one_line[:200]}{'…' if len(one_line) > 200 else ''}")
        print(f"  {r['url']}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Search arxiv.org")
    ap.add_argument("--query", required=True, help="search query (uses arxiv query syntax)")
    ap.add_argument("--max", type=int, default=10, help="max results (default 10)")
    ap.add_argument("--since", type=int, default=None, help="only papers submitted since YYYY")
    ap.add_argument("--cat", action="append", default=[], help="category filter (can be repeated; OR semantics)")
    ap.add_argument("--sort", choices=["relevance", "submittedDate", "updatedDate"], default="relevance")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    ap.add_argument("--delay", type=float, default=3.0, help="seconds between requests (be polite)")
    args = ap.parse_args()

    t0 = time.time()
    results = search(args.query, max_results=args.max, since_year=args.since,
                     categories=args.cat or None, sort_by=args.sort)
    elapsed = time.time() - t0

    if args.json:
        json.dump({"query": args.query, "elapsed_sec": round(elapsed, 2),
                   "results": results}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print_human(results, args.query)
    return 0


if __name__ == "__main__":
    sys.exit(main())
