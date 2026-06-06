# Search Tips — Practical Notes

Things the SKILL.md can't say without making it too long.

## The local search is substring, not semantic

`/api/agent/search` does **case-insensitive substring matching** across:
- `display` title
- tag list (joined as a string)
- first 300 characters of the abstract

Concretely, this means:
- `"SNN"` matches `"spiking neural network"` only if the literal string "snn" appears in the title/abstract. It usually does (most abstracts use the acronym), but not always.
- `"脉冲"` (Chinese) **does** match — the search is Unicode-aware and case-insensitive, but **not** locale-aware (no word boundaries for CJK).
- `"transform"` matches `"transformer"` and `"transformation"`, but **not** `"trans form"`.

So: pick search terms that are **likely to literally appear** in the paper. The LLM-powered `/api/ai/search` in the UI is the right tool for "I want anything about X" — tell the user to run that, or pass the term to the LLM and have it suggest 3-5 alternative literal substrings to try.

## Multi-step search pattern

When a single search misses but you suspect the paper exists, escalate:

1. `GET /api/agent/papers` → scan titles for partial matches.
2. If found, `GET /api/agent/papers/{name}` → confirm the abstract.
3. If not found locally, switch to `whiskershelf-web-search`.

This is faster than iterating search queries with synonyms.

## When tags are the right index

If the user has a strong taxonomy (the default 24+ presets + custom), tags can be a more reliable index than full-text search:
- "Show me everything tagged `世界模型`" — read the catalog, filter by tag in your head.
- "What has the user been reading on `线性注意力` recently?" — list, then check `paper_reading.json` for the user's read counts.

Tags also encode the **user's mental model**, not the paper's subject — when in doubt, prefer tags.

## When `notes` matters more than `abstract`

`abstract` is what the paper's authors wrote. `notes` is what the **user** wrote while reading. If the user says "the paper where I noted X", search the user's notes, not the abstract. The Agent API does not index notes in `/search` (only abstract_preview), so:

1. `GET /api/agent/papers` to get a name list.
2. `GET /api/agent/papers/{name}` for each candidate — read the `notes` field.

This is also why the SKILL.md says "fetch the full abstract + notes, not just preview".

## Chinese filenames

The library contains many papers with Chinese characters in their filenames (e.g. `修改黑猫走路姿势.png` style, or pure-Chinese PDF names). The Agent API requires the filename to be URL-encoded. The shell helpers in `scripts/ws_*.py` do this automatically.

If you must call the API directly:
```python
import urllib.parse, urllib.request
name = "脉冲神经网络综述.pdf"
url = f"http://127.0.0.1:8080/api/agent/papers/{urllib.parse.quote(name)}"
urllib.request.urlopen(url).read()
```

## Concurrency

The server is single-threaded `http.server`. Don't fire 100 parallel requests; you'll queue them. Sequential is fine, and matches how an agent actually searches (one query → one decision → next query).

## Caching the response in the agent

Once you fetch a paper's full record, keep it in your context. The cost of re-fetching is low, but the **risk of fetches drifting mid-session** (the user adds a paper, changes a tag, edits notes) is real. If the user says "wait, my notes on X say Y now" — re-fetch, don't trust your earlier read.
