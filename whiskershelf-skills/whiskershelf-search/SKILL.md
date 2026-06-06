---
name: whiskershelf-search
description: Search the user's local WhiskerShelf paper library. Use when the user references a paper by partial title, asks "find papers about X", or needs to retrieve the full abstract/notes of a specific paper.
---

# Whiskershelf Search

WhiskerShelf runs locally on `http://127.0.0.1:8080`. **It only responds when the user has the app open.** If any call fails or returns empty, the very first thing to do is ask the user to start WhiskerShelf — do not silently fall back to web search (that's a different skill: `whiskershelf-web-search`).

## Endpoints (Agent API)

```
POST  http://127.0.0.1:8080/api/agent/search
Body  : {"query": "spiking neural networks for time series"}
→     : {"results": [{name, title, abstract_preview}, ...]}   # max 20

GET   http://127.0.0.1:8080/api/agent/papers
→     : {"papers": [{name, title, tags, abstract_preview}, ...]}

GET   http://127.0.0.1:8080/api/agent/papers/{name}
→     : {name, title, abstract, tags, notes}

GET   http://127.0.0.1:8080/api/agent/papers/{name}/tags
→     : {"tags": ["linear-attention", "snn", ...]}
```

The full reference (request/response shapes, error codes, gotchas) is in `references/api-endpoints.md`.

## When to use which endpoint

| You want to… | Endpoint |
|---|---|
| Find papers about a topic (any size of match) | `POST /api/agent/search` |
| List everything in the library (e.g. "what do I have?") | `GET /api/agent/papers` |
| Get the full abstract + notes for one paper | `GET /api/agent/papers/{name}` |
| Read the current tags on a paper | `GET /api/agent/papers/{name}/tags` |
| **Add / change tags** (use `whiskershelf-tag` instead — gated) | `POST /api/agent/papers/{name}/tags` |

`{name}` is the **PDF filename** including `.pdf` extension. It must be URL-encoded if it contains non-ASCII characters or spaces (Chinese filenames in this library are common).

## Shell helpers (in `scripts/`)

These wrap the endpoints so you can run them from a terminal without crafting JSON by hand. They are also useful for one-off spot-checks during long sessions.

```bash
# Cross-platform (works on Windows + macOS + Linux) — uses only Python stdlib
python .claude/skills/whiskershelf-search/scripts/ws_search.py "spiking neural network"
python .claude/skills/whiskershelf-search/scripts/ws_papers.py
python .claude/skills/whiskershelf-search/scripts/ws_detail.py "Spikformer v2.pdf"
python .claude/skills/whiskershelf-search/scripts/ws_tags_get.py "Spikformer v2.pdf"
```

For the Bash tool, prefer the `ws_*.sh` wrappers (or the `.ps1` ones on Windows) — see `scripts/`.

## When to search

- **Before starting work on a brief direction** — search for related work the user might already have read but didn't surface in the brief. Papers in the library carry user notes and tags that often change the approach.
- **User says "my X paper" / "the paper about Y"** — search by partial title, then fetch the abstract.
- **User asks "what's in my library?"** — use `GET /papers`.
- **A direction requires deep context** (e.g., "implement the method from paper X"): fetch the full abstract + notes via `GET /papers/{name}`. Don't guess from a 300-char preview alone.
- **Before recommending a tag**, look at the paper's existing tags first (`GET /papers/{name}/tags`) — match the user's mental model, don't impose your own.

## When NOT to use

- **Don't search for "all ML papers" or "the field of X"** — the local library is small and personal. Use `whiskershelf-web-search` for broad coverage.
- **Don't call `/api/agent/papers` in a loop** to find a single paper. Use `/search` first.
- **Don't mutate tags** from this skill — go to `whiskershelf-tag`. That skill enforces user confirmation; this one doesn't.

## Research-process guidance

After every search, ask yourself: "Does this change the direction we're pursuing?" If yes, surface it to the user before continuing. Search is a **research move, not a routine** — every search result is a chance to refine the plan.

If a search returns nothing, that's also information:
- The user doesn't have that paper — recommend `whiskershelf-web-search`.
- The user's library is mis-tagged (e.g., the paper exists but is tagged "Transformer" and the search missed it) — consider `GET /papers` to scan titles.
- The search index in `/api/agent/search` is **substring-only** (case-insensitive, across title + tags + first 300 chars of abstract). It does **not** call the LLM. If the term doesn't literally appear, it won't match. For semantic matching, use the UI's `🔍 AI 语义搜索` (the user's `/api/ai/search`) and tell the user to do it in the browser.

See `examples/queries.md` for a worked example of multi-step searching.
