#!/usr/bin/env python3
"""
fetch_paper.py — Fetch metadata for a single paper by arxiv id or DOI.

Routes to arxiv for preprint ids, Semantic Scholar for DOIs / general lookup.
Stdlib-only.

Usage:
    python fetch_paper.py --arxiv 2410.01234
    python fetch_paper.py --doi 10.1109/CVPR.2024.00123
    python fetch_paper.py --arxiv 2410.01234 --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any


def fetch_arxiv(arxiv_id: str) -> dict[str, Any] | None:
    """Fetch an arxiv paper by id (e.g. 2410.01234 or 2410.01234v2)."""
    arxiv_id = arxiv_id.strip()
    arxiv_id = re.sub(r"^arxiv:", "", arxiv_id, flags=re.IGNORECASE)

    url = f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}"
    req = urllib.request.Request(url, headers={"User-Agent": "whiskershelf-web-search/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except Exception as e:
        print(f"arxiv lookup failed: {e}", file=sys.stderr)
        return None

    NS = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    for entry in root.findall("atom:entry", NS):
        title_el = entry.find("atom:title", NS)
        summary_el = entry.find("atom:summary", NS)
        id_el = entry.find("atom:id", NS)
        published_el = entry.find("atom:published", NS)
        authors = [(a.find("atom:name", NS).text or "").strip()
                   for a in entry.findall("atom:author", NS)
                   if a.find("atom:name", NS) is not None]
        cats = [(c.attrib.get("term") or "").strip()
                for c in entry.findall("atom:category", NS)]
        if id_el is None or id_el.text is None:
            continue
        m = re.search(r"abs/(.+)$", id_el.text)
        full_id = m.group(1) if m else arxiv_id
        published = (published_el.text or "").strip() if published_el is not None else ""
        return {
            "source": "arxiv",
            "arxiv_id": full_id,
            "title": re.sub(r"\s+", " ", (title_el.text or "")).strip() if title_el is not None else "",
            "authors": authors,
            "summary": re.sub(r"\s+", " ", (summary_el.text or "")).strip() if summary_el is not None else "",
            "published": published,
            "year": published[:4],
            "categories": cats,
            "abs_url": f"https://arxiv.org/abs/{full_id}",
            "pdf_url": f"https://arxiv.org/pdf/{full_id}",
        }
    return None


def fetch_doi(doi: str) -> dict[str, Any] | None:
    """Resolve a DOI via the public Crossref API (no key required)."""
    doi = doi.strip()
    doi = re.sub(r"^doi:", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    req = urllib.request.Request(url, headers={"User-Agent": "whiskershelf-web-search/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"crossref lookup failed: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"crossref lookup failed: {e}", file=sys.stderr)
        return None

    msg = data.get("message") or {}
    authors = []
    for a in msg.get("author") or []:
        name = " ".join(filter(None, [a.get("given"), a.get("family")]))
        if name:
            authors.append(name)
    title = msg.get("title") or []
    title_str = title[0] if title else ""
    abstract = msg.get("abstract", "")
    # Crossref abstracts often have JATS XML; strip tags.
    abstract = re.sub(r"<[^>]+>", "", abstract).strip()
    issued = msg.get("issued", {}).get("date-parts", [[None]])[0]
    year = str(issued[0]) if issued and issued[0] else ""
    container = (msg.get("container-title") or [""])[0]
    links = msg.get("link") or []
    pdf_url = ""
    for l in links:
        if l.get("content-type") == "application/pdf":
            pdf_url = l.get("URL", "")
            break
    return {
        "source": "crossref",
        "doi": doi,
        "title": title_str,
        "authors": authors,
        "summary": abstract,
        "year": year,
        "venue": container,
        "abs_url": f"https://doi.org/{doi}",
        "pdf_url": pdf_url,
    }


def print_human(p: dict[str, Any] | None) -> None:
    if p is None:
        print("(not found)")
        return
    print(f"# {p.get('title', '(no title)')}")
    if p.get("arxiv_id"):
        print(f"arXiv: {p['arxiv_id']}  ({p.get('year', '?')})")
    if p.get("doi"):
        print(f"DOI: {p['doi']}  ({p.get('year', '?')})")
    if p.get("venue"):
        print(f"Venue: {p['venue']}")
    print(f"Authors: {', '.join(p.get('authors') or [])[:200]}")
    if p.get("categories"):
        print(f"Categories: {', '.join(p['categories'])}")
    print()
    print(p.get("summary") or "(no abstract)")
    print()
    if p.get("abs_url"):
        print(f"abstract: {p['abs_url']}")
    if p.get("pdf_url"):
        print(f"pdf:      {p['pdf_url']}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch one paper's metadata")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--arxiv", help="arxiv id (e.g. 2410.01234)")
    src.add_argument("--doi", help="DOI (e.g. 10.1109/CVPR.2024.00123)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.arxiv:
        paper = fetch_arxiv(args.arxiv)
    else:
        paper = fetch_doi(args.doi)

    if args.json:
        json.dump(paper, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print_human(paper)
    return 0 if paper else 2


if __name__ == "__main__":
    sys.exit(main())
