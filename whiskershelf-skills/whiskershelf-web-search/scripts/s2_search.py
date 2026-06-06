#!/usr/bin/env python3
"""
s2_search.py — Search Semantic Scholar and return structured results.

Stdlib-only. Uses the public Graph API:
    https://api.semanticscholar.org/graph/v1/paper/search

Optional API key via env var S2_API_KEY (recommended for higher rate limits).

Usage:
    python s2_search.py --query "RWKV-7 state evolution"
    python s2_search.py --query "linear attention" --max 5 --min-citations 50
    python s2_search.py --query "Mamba" --year 2024 --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Any


S2_BASE = "https://api.semanticscholar.org/graph/v1"


def search(query: str, *, max_results: int = 10, year: str | None = None,
           min_citations: int | None = None, fields: list[str] | None = None) -> dict[str, Any]:
    if fields is None:
        fields = ["title", "abstract", "year", "venue", "publicationVenue",
                  "authors.name", "citationCount", "influentialCitationCount",
                  "externalIds", "url", "openAccessPdf"]
    params = {
        "query": query,
        "limit": max_results,
        "fields": ",".join(fields),
    }
    if year:
        params["year"] = year  # e.g. "2024" or "2023-2025"
    if min_citations is not None:
        params["minCitationCount"] = min_citations

    url = S2_BASE + "/paper/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"s2 request failed: {e}", file=sys.stderr)
        return {"data": [], "total": 0}


def fetch_by_arxiv(arxiv_id: str) -> dict[str, Any] | None:
    """Fetch a single paper by arxiv id (e.g. 2410.01234 or 'arXiv:2410.01234')."""
    if arxiv_id.lower().startswith("arxiv:"):
        arxiv_id = arxiv_id.split(":", 1)[1]
    url = f"{S2_BASE}/paper/arXiv:{arxiv_id}?fields=title,abstract,year,venue,authors.name,citationCount,externalIds,url,openAccessPdf"
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception as e:
        print(f"s2 lookup failed: {e}", file=sys.stderr)
        return None


def _headers() -> dict[str, str]:
    h = {"User-Agent": "whiskershelf-web-search/1.0"}
    if os.environ.get("S2_API_KEY"):
        h["x-api-key"] = os.environ["S2_API_KEY"]
    return h


def _print(p: dict[str, Any], idx: int) -> None:
    ext = p.get("externalIds") or {}
    arxiv = ext.get("ArXiv") or ext.get("arXiv") or ""
    doi = ext.get("DOI") or ""
    authors = ", ".join((a.get("name") or "") for a in (p.get("authors") or [])[:3])
    extra = f"  (+{len(p.get('authors') or []) - 3})" if len(p.get("authors") or []) > 3 else ""
    venue = p.get("venue") or p.get("publicationVenue") or "?"
    oa = p.get("openAccessPdf") or {}
    oa_url = oa.get("url", "") if isinstance(oa, dict) else ""
    cite = p.get("citationCount", 0)
    influential = p.get("influentialCitationCount", 0)
    print(f"[{idx}] {p.get('title', '(no title)')}")
    print(f"    {authors}{extra}  ({p.get('year', '?')}, {venue})")
    print(f"    cited by: {cite}  (influential: {influential})")
    if arxiv:
        print(f"    arXiv:{arxiv}")
    if doi:
        print(f"    doi: {doi}")
    if oa_url:
        print(f"    pdf:  {oa_url}")
    abstract = (p.get("abstract") or "").replace("\n", " ")
    if abstract:
        print(f"    {abstract[:240]}{'…' if len(abstract) > 240 else ''}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Search Semantic Scholar")
    ap.add_argument("--query", help="search query (omit if --arxiv-id is given)")
    ap.add_argument("--arxiv-id", help="fetch one paper by arxiv id (e.g. 2410.01234)")
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--year", help="year filter, e.g. '2024' or '2023-2025'")
    ap.add_argument("--min-citations", type=int, help="only papers with >= N citations")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.arxiv_id:
        t0 = time.time()
        paper = fetch_by_arxiv(args.arxiv_id)
        elapsed = time.time() - t0
        if args.json:
            json.dump({"elapsed_sec": round(elapsed, 2), "paper": paper}, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        else:
            if paper is None:
                print(f"(no S2 record for arXiv:{args.arxiv_id})")
            else:
                _print(paper, 1)
        return 0

    if not args.query:
        ap.error("either --query or --arxiv-id is required")

    t0 = time.time()
    resp = search(args.query, max_results=args.max, year=args.year, min_citations=args.min_citations)
    elapsed = time.time() - t0
    papers = resp.get("data") or []
    if args.json:
        json.dump({"query": args.query, "elapsed_sec": round(elapsed, 2),
                   "total": resp.get("total"), "papers": papers},
                  sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        if not papers:
            print(f"(no S2 results for '{args.query}')")
            return 0
        print(f"{len(papers)} S2 result(s) for '{args.query}' (total match: {resp.get('total', '?')}):\n")
        for i, p in enumerate(papers, 1):
            _print(p, i)
    return 0


if __name__ == "__main__":
    sys.exit(main())
