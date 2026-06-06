# Where to Search — A Decision Tree

This is a quick lookup: "I need to find X, where do I go first?" Use it before each new search to avoid spending a query in the wrong place.

## Decision tree

```
I need to find…
├── a recent preprint (last 18 months)            → arxiv
├── the most-cited work on a topic                 → Semantic Scholar
├── an accepted conference paper w/ reviews        → OpenReview
├── a paper + its open-source code                 → Papers With Code
├── a specific paper I already know the title of   → arxiv (title search) → S2 (fallback)
├── a specific author’s recent work                → arxiv (au:"<name>") or Google Scholar
├── the latest SOTA on benchmark X                 → Papers With Code leaderboard
└── a paywalled venue version of a paper           → arxiv first (likely has preprint)
```

## Venue-by-venue detail

### arxiv.org
- **Best for**: preprints, fresh signal, broad ML/AI/CS coverage.
- **URL**: `https://arxiv.org/abs/<id>` for landing; `https://arxiv.org/pdf/<id>` for PDF.
- **API**: `https://export.arxiv.org/api/query?search_query=...&start=0&max_results=10`
- **Rate limit**: be polite (~1 request/second); the `scripts/arxiv_search.py` CLI includes a small delay between paginated calls.
- **See**: `references/arxiv-categories.md` for category codes.

### Semantic Scholar
- **Best for**: citation graph, "papers citing X", semantic search, paper metadata by DOI/arXiv ID.
- **URL**: `https://www.semanticscholar.org/paper/<id>`
- **Graph API** (free, key optional for low volume):
  - Search: `https://api.semanticscholar.org/graph/v1/paper/search?query=<q>&limit=10&fields=title,authors,year,abstract,url,citationCount`
  - Lookup: `https://api.semanticscholar.org/graph/v1/paper/arxiv:<id>?fields=...`
  - Citations: `https://api.semanticscholar.org/graph/v1/paper/<id>/citations?fields=...`
- **Rate limit**: ~100 requests/5 min without an API key. The `scripts/s2_search.py` CLI handles a free key via `S2_API_KEY` env var.
- **Tip**: `?minCitationCount=N` is the easiest "is this paper influential?" filter.

### OpenReview
- **Best for**: NeurIPS, ICML, ICLR, ICLR 2024+, UAI, COLM accepted papers, reviews, and discussion.
- **URL**: `https://openreview.net/forum?id=<id>` for paper, `https://api.openreview.net` for API.
- **API**: notes API is open for public venues; ACL papers are also indexed.
- **Tip**: search by title fragment; OpenReview is excellent for "did this paper pass peer review" questions.

### Papers With Code
- **Best for**: paper ↔ code pairing, SOTA leaderboards, dataset links.
- **URL**: `https://paperswithcode.com/paper/<slug>` for paper; `https://paperswithcode.com/sota/<task>` for leaderboards.
- **API**: `https://paperswithcode.com/api/v1/papers/?q=<title>`. Free but rate-limited.
- **Tip**: when the user asks "is there code for X?" this is the first stop.

### Google Scholar
- **Best for**: broadest coverage; paywalled venue papers; author disambiguation.
- **URL**: `https://scholar.google.com/scholar?q=<query>`
- **No API** — use the `WebSearch` tool with `site:scholar.google.com`.
- **Tip**: when arxiv and S2 both come up empty, try Scholar. The user's library may have older / paywalled papers that aren't on arxiv.

### Conference proceedings
- **Best for**: the official, final version of an accepted paper.
- **URLs by venue**:
  - NeurIPS: `https://papers.nips.cc`
  - ICML: `https://proceedings.mlr.press`
  - ICLR: see OpenReview
  - CVPR / ICCV / ECCV: `https://openaccess.thecvf.com`
  - ACL / EMNLP / NAACL: `https://aclanthology.org`
  - IEEE Trans.: `https://ieeexplore.ieee.org` (often paywalled, search arxiv for preprint)
- **Tip**: only fall back to proceedings if you need the published version (e.g., for citation) — the arxiv preprint is usually identical modulo formatting.

## Quick API one-liners

```bash
# arxiv: latest 5 in cs.LG mentioning "spiking"
curl -s "http://export.arxiv.org/api/query?search_query=cat:cs.LG+AND+abs:%22spiking%22&max_results=5&sortBy=submittedDate&sortOrder=descending" \
  | grep -E '<title>|<id>'

# Semantic Scholar: papers citing "Attention is all you need" (arXiv:1706.03762)
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:1706.03762/citations?fields=title,year,url&limit=5"
```

## When to use the browser (WebFetch) instead of the API

- The paper isn't on arxiv or S2 (rare; old books, theses).
- You need to read the **PDF** to extract something the abstract doesn't say (e.g., specific hyperparameters, dataset details).
- You're on OpenReview and want the **reviews** (the API exposes some of this, but the web UI is friendlier for browsing discussion).

## Anti-patterns

- Going to Google Scholar first. Always start with arxiv or S2 — the API gives you structured JSON, the API responses are way easier to process than scraping HTML.
- Re-running the same query across 4 venues. Pick the right venue once; trust it.
- Forgetting that the user might already have the paper locally. Check `whiskershelf-search` first, then web.
