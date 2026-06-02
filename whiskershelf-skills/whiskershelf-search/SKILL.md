---
name: whiskershelf-search
description: Search the user's local WhiskerShelf paper library. Use when the user references a paper by partial title, or asks "find papers about X".
---

# Whiskershelf Search

WhiskerShelf runs locally on http://127.0.0.1:8080. **It only responds when the user has the app open.** If a search call fails, ask the user to start WhiskerShelf.

## Endpoints

```
POST http://127.0.0.1:8080/api/agent/search
Body: {"query": "spiking neural networks for time series"}
→ {"results": [{name, title, abstract_preview}, ...]}

GET  http://127.0.0.1:8080/api/agent/papers
→ {"papers": [{name, title, tags, abstract_preview}, ...]}

GET  http://127.0.0.1:8080/api/agent/papers/{name}
→ {name, title, abstract, tags, notes}
```

## When to search

- **Before starting work**: search for related work the user might already have read but didn't surface in the brief.
- **User says "my X paper"**: search by partial title, then fetch the abstract.
- **User asks "what's in my library"**: use `GET /papers`.
- **Direction requires deep context** (e.g., "implement the method from paper X"): fetch the full abstract via `GET /papers/{name}`.

## Research-process guidance

After every search, ask yourself: "Does this change the direction we're pursuing?" If yes, surface it to the user before continuing. Search is a research move, not a routine.
