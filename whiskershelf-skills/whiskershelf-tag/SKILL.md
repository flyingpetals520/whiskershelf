---
name: whiskershelf-tag
description: Read/write tags on papers in the user's local WhiskerShelf library. Use to organize new artifacts or re-tag after a research session.
---

# Whiskershelf Tag Operations

The user has a 24+ taxonomy of preset tags. Use them; don't invent new ones unless necessary.

## Endpoints

```
GET    http://127.0.0.1:8080/api/agent/papers/{name}/tags
→ {"tags": ["linear-attention", "snn", ...]}

POST   http://127.0.0.1:8080/api/agent/papers/{name}/tags
Body: {"tags": ["snn", "brain-inspired"]}
→ {"success": true, "tags": [...]}

GET    http://127.0.0.1:8080/api/presets
→ {"presets": ["Agent", "Transformer", "大语言模型 LLM", ...]}
```

## When to tag

- **After completing a research direction** — ask the user if they want to tag any newly-relevant papers.
- **User adds a new paper to the library** — suggest 1-3 tags from the preset list.
- **User says "X is now important" or "stop reading Y"** — adjust tags accordingly.

## Research-process guidance

Tagging is how the user remembers. Don't tag silently. Always:
1. Show the proposed tag change
2. Wait for user confirmation
3. Confirm what was actually written

If a tag isn't in the presets, ask the user before creating a new one (avoid tag sprawl).
