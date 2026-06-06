# WhiskerShelf Agent API Reference

The endpoints under `/api/agent/*` are designed for **machine consumers** (Claude Code, scripts). They are deliberately a small, stable surface — no LLM is called server-side, so the responses are fast and deterministic.

Base URL: `http://127.0.0.1:8080` (configurable in `app.py`; the port is 8080 by default).

## Conventions

- All responses are JSON with `Content-Type: application/json; charset=utf-8`.
- CORS is wide open (`Access-Control-Allow-Origin: *`) — this is intentional for local dev.
- Errors are JSON of the form `{"error": "<message>"}` with an appropriate HTTP status code.
- `{name}` in the URL path is the **PDF filename**, **URL-encoded**. Chinese characters and spaces must be percent-encoded (`urllib.parse.quote`).

## `POST /api/agent/search`

Substring search across title, tags, and the first 300 characters of the abstract.

### Request
```json
{"query": "spiking neural network"}
```

### Response (200)
```json
{
  "results": [
    {
      "name": "Spikformer v2.pdf",
      "title": "Spikformer v2",
      "abstract_preview": "Spiking Neural Networks (SNNs) ..."
    }
  ]
}
```

- Capped at **20** results.
- Empty `query` returns `{"results": []}` (no error).
- No LLM is invoked.

### When this returns nothing

The index is **substring-based and zero-cost**. If you have a paper in the library but it doesn't appear here, possible causes:
- Title/abstract doesn't literally contain your term (the field is tagged but the abstract uses synonyms).
- The PDF hasn't been re-scanned — ask the user to click 🔄 in the UI.
- The paper was added with a non-PDF name (e.g., `.PDF` uppercase — handled, but weird characters can trip up).

If you suspect the paper exists but isn't matched, fall back to `GET /api/agent/papers` and grep the title list yourself.

## `GET /api/agent/papers`

List all papers with a short summary.

### Response (200)
```json
{
  "papers": [
    {
      "name": "Spikformer v2.pdf",
      "title": "Spikformer v2",
      "tags": ["脉冲神经网络 SNN", "Transformer"],
      "abstract_preview": "Spiking Neural Networks (SNNs) ..."
    }
  ]
}
```

- `title` falls back to `name` (the filename) if no `display` title is stored.
- This endpoint reads from in-memory cache; safe to call repeatedly.

## `GET /api/agent/papers/{name}`

Full record for a single paper.

### Response (200)
```json
{
  "name": "Spikformer v2.pdf",
  "title": "Spikformer v2",
  "abstract": "Spiking Neural Networks (SNNs) ... (full text)",
  "tags": ["脉冲神经网络 SNN", "Transformer"],
  "notes": "user-written notes here"
}
```

### Error cases
- `400 {"error": "invalid name"}` — empty or malformed name.
- `404 {"error": "not found"}` — the paper isn't in the library.

## `GET /api/agent/papers/{name}/tags`

Read-only fetch of just the tags.

### Response (200)
```json
{"tags": ["脉冲神经网络 SNN", "Transformer"]}
```

### Error cases
- `404 {"error": "not found"}` — paper doesn't exist (not "no tags"; an empty list is `{"tags": []}`).

## `POST /api/agent/papers/{name}/tags`

**Gated write** — this skill's contract is "show user, get confirmation, then write". See `whiskershelf-tag` for the proper workflow; the endpoint itself does not enforce gating.

### Request
```json
{"tags": ["脉冲神经网络 SNN", "架构创新"]}
```

### Behavior
- Tags are stripped, deduplicated, and **fully replace** the existing list (not merged).
- Audit-logged to server console: `[Agent API] tags updated for {name}: [...]`.
- Empty list clears the paper's tags.

### Error cases
- `400 {"error": "invalid json"}` — malformed body.
- `400 {"error": "tags must be list"}` — `tags` field is not a JSON array.
- `404 {"error": "paper not found"}` — paper doesn't exist.

## Rate limits / best practices

There are no hard rate limits (this is a local personal server), but:

- **Don't** call `GET /api/agent/papers` more than once per session unless the user adds new PDFs.
- **Do** cache results in your conversation — if you've already fetched a paper's abstract, don't re-fetch unless you suspect it changed.
- **Do** use the smallest sufficient endpoint. `/search` is cheaper than `/papers` for finding a topic.

## Versioning

The API has no formal version. The shape of returned objects is the contract — if WhiskerShelf needs to break it, a new prefix (`/api/agent/v2/...`) will be added. The current shape is stable as of v1.x.
