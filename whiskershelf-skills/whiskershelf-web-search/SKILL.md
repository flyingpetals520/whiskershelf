---
name: whiskershelf-web-search
description: Search the broader open literature (arxiv, Semantic Scholar, OpenReview, Papers With Code) for academic papers to supplement the user's local WhiskerShelf library. Use when the local library is missing key references, when the user asks about a paper outside the library, or when validation against the wider literature is needed.
---

# Whiskershelf Web Search

WhiskerShelf's `whiskershelf-search` skill only finds papers the user has already collected. This skill extends coverage to the **open literature**, so you can verify the brief against current state-of-the-art, fill in missing citations, and ground the work in the broader research conversation.

You have a `WebSearch` tool (or `WebFetch` for specific URLs). Use it. The shell scripts in `scripts/` give you a structured CLI on top of `arxiv.org` and `Semantic Scholar` so you can search and download with a single command.

## When to use

- **The brief references a method/paper the user doesn't have locally.** Example: brief says "use the loss from Smith et al. 2023" but `whiskershelf-search` returns nothing — go to the web.
- **The user asks "is there more recent work on X?"** — local library only has what the user added; web has everything.
- **The chosen research direction needs ground-truth validation.** Before committing to an implementation, check that no one has already done it (and if they have, cite them).
- **The user says "I need to see if this has been tried"** or any phrasing that implies "look beyond my library."
- **A new paper came out after the user's library was last updated** (e.g., user has 2024 papers but wants 2026 SOTA).

**Don't use** for:
- Routine search within the user's library (that's `whiskershelf-search`).
- Trivia, general knowledge, or non-academic questions.
- Questions already answered by the local library.
- Downloading PDFs the user didn't ask for — fetching the abstract is enough to decide.

## Recommended search venues (in priority order)

| Venue | Best for | Free? | See |
|---|---|---|---|
| **arxiv.org** | Preprints, freshest signal, esp. ML/AI | yes | `references/arxiv-categories.md`, `scripts/arxiv_search.py` |
| **Semantic Scholar** | Citation graph, "papers citing X", semantic search | yes (rate-limited) | `references/venues.md`, `scripts/s2_search.py` |
| **OpenReview** | NeurIPS / ICML / ICLR accepted papers, reviews | yes | `references/venues.md` |
| **Papers With Code** | Paper + code pairing, benchmark leaderboards | yes | `references/venues.md` |
| **Google Scholar** | Broadest coverage, no API | yes (no API) | fall back to `WebSearch` |
| **Conference proceedings** | Latest year, official version | yes | `references/venues.md` |

When in doubt, **arxiv first** — it's the fastest, most open, and covers ~90% of ML/AI preprints within days of submission. Semantic Scholar second for citation context.

## Research workflow

1. **Form a precise search query.** Combine the concept, method, dataset, and year range. Examples:
   - `"spiking neural network associative memory 2024..2026"`
   - `"Gated DeltaNet Mamba-3 hybrid attention"`
   - `"value iteration network autonomous driving arxiv"`
   - Add `site:arxiv.org` or `site:openreview.net` to constrain to academic venues.

2. **Run 2–4 searches with different angles.** One query rarely surfaces the full landscape. Try:
   - The original method/term
   - A related/competing term
   - Recent (last 12–18 months) only
   - Top-cited (use Semantic Scholar with `?minCitationCount=N` for "papers with traction")

3. **For each promising result, fetch the abstract or paper page** with `WebFetch`, or call the structured API via the `scripts/` CLI. Extract:
   - Title, authors, year, venue
   - Abstract (one paragraph)
   - Why it matters for the user's research direction
   - URL

4. **Synthesize a "Related External Work" section** and add it to the research context. Format:
   ```
   ### Related external work (from whiskershelf-web-search)
   - **<Title>** (<Year>, <Venue>): <one-sentence takeaway>. <URL>
   - ...
   ```

5. **If you find a paper that DIRECTLY enables or invalidates the chosen direction**, surface it to the user immediately with a short paragraph: "I found <X> which already does <Y>. This affects the direction. Want to (a) pivot, (b) differentiate from it explicitly, or (c) proceed and cite it?"

6. **Update `brief.md` (or the working notes) with the new references.** Don't keep the synthesis in conversation context only — it will get compressed and lost.

## Shell helpers (in `scripts/`)

The web-search CLI scripts use only Python stdlib + the public APIs of arxiv.org and semanticscholar.org. They save you a WebSearch round-trip when you want a structured result.

```bash
# arxiv search
python .claude/skills/whiskershelf-web-search/scripts/arxiv_search.py \
    --query "spiking neural network associative memory" \
    --max 10 --since 2024

# Semantic Scholar search
python .claude/skills/whiskershelf-web-search/scripts/s2_search.py \
    --query "RWKV-7 state evolution" --max 5

# Fetch metadata for an arxiv id
python .claude/skills/whiskershelf-web-search/scripts/fetch_paper.py --arxiv 2410.01234

# Fetch metadata for a DOI or title
python .claude/skills/whiskershelf-web-search/scripts/fetch_paper.py --doi "10.1109/CVPR.2024.00123"
```

## Token economy

Web results are noisy. Don't paste full abstracts into context — quote 1–2 sentences that matter, then reference the URL. The user can read the full paper via the file manager or fetch the URL themselves.

## Tone

You are a **research scout**, not a search engine. Be opinionated about which results matter; ignore off-topic noise without listing it. When you find a key paper, say so directly — "this is the one to read next" is more useful than a balanced list of 10.

See `examples/queries.md` for a worked example of a multi-query search session.
