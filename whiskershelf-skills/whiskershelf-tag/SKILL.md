---
name: whiskershelf-tag
description: Read and write tags on papers in the user's local WhiskerShelf library. Use after completing a research direction, when the user adds a new paper, or to re-tag after a session. **Writes are gated — always confirm with the user before calling the write endpoint.**
---

# Whiskershelf Tag Operations

The user has a 27-preset tag taxonomy (see `references/tag-taxonomy.md`) + the freedom to add custom tags. **Use presets when possible.** Don't invent new tags unless necessary — taxonomy drift makes future search worse.

The rule that distinguishes this skill from a free-form `POST` is **gating**: every write goes through three steps (propose → confirm → execute → confirm-after).

## Endpoints (Agent API)

```
GET    http://127.0.0.1:8080/api/agent/papers/{name}/tags
→      {"tags": ["线性注意力", "脉冲神经网络 SNN", ...]}

POST   http://127.0.0.1:8080/api/agent/papers/{name}/tags
Body   {"tags": ["脉冲神经网络 SNN", "架构创新"]}
→      {"success": true, "tags": [...]}     # tags fully REPLACE the existing list

GET    http://127.0.0.1:8080/api/presets
→      {"presets": ["Agent", "Transformer", "大语言模型 LLM", ...]}
```

The server logs every successful write to stdout (`[Agent API] tags updated for {name}: [...]`) for audit.

For full request/response/error shapes see `references/api-endpoints.md` (cross-skill reference, lives in `whiskershelf-search/references/`).

## The gating workflow (always)

```
1. READ     GET /api/agent/papers/{name}              (current state)
            GET /api/agent/papers/{name}/tags         (current tags)
            GET /api/agent/presets                    (the preset list)

2. PROPOSE  Build the proposed tag list. Prefer:
              - existing tags the paper already has (no churn)
              - presets from the catalog (use `check_presets.sh`)
              - existing custom tags from other papers (consistency)
            Avoid: 1-word generic tags ("AI", "ML", "important"),
                   tag sprawl, near-duplicates of presets.

3. CONFIRM  Show the user:
              Paper: <title>
              Current tags: <list>
              Proposed: <list>  (additions in green, removals strikethrough)
            Ask: "Apply these tag changes? (yes / adjust / skip)"

4. EXECUTE  POST /api/agent/papers/{name}/tags with the new list.
            The API REPLACES the entire list (not a merge) — so include
            the tags you want to KEEP plus the tags you want to ADD.

5. CONFIRM-AFTER Read back GET /api/agent/papers/{name}/tags, show
            the user, and stop.
```

The server doesn't enforce gating — that's this skill's job. Skipping step 3 means a silent destructive write, which is the failure mode this skill exists to prevent.

## When to tag

- **After completing a research direction** — ask the user if they want to tag any newly-relevant papers (or new artifacts the user has saved alongside the project).
- **User adds a new paper to the library** — suggest 1–3 tags from the preset list, derived from the abstract.
- **User says "X is now important" or "stop reading Y"** — adjust tags accordingly. "Important" maps to a star/flag, not a tag; respect the user's mental model.
- **The user explicitly asks you to organize** — propose a batch re-tag of related papers.

## When NOT to tag

- **Don't tag silently.** Even if the proposed change seems obvious, surface it.
- **Don't tag for the user's sake** ("I think this is relevant") — wait for the user to express the need.
- **Don't merge similar tags** (`SNN` vs `脉冲神经网络 SNN`) without asking — the user may have intentionally kept them distinct.
- **Don't add a new custom tag** without listing existing options and asking the user to confirm.

## Shell helpers (in `scripts/`)

```bash
# Read current tags
python .claude/skills/whiskershelf-tag/scripts/ws_tags_get.py "Spikformer v2.pdf"

# Propose: check whether a candidate tag is in the preset list
python .claude/skills/whiskershelf-tag/scripts/check_presets.py "脉冲神经网络 SNN"

# Compare your proposed list against the preset list and current tags
python .claude/skills/whiskershelf-tag/scripts/check_presets.py --propose "SNN,brain-inspired,custom-tag"

# Write tags (after the gating workflow above)
python .claude/skills/whiskershelf-tag/scripts/ws_tags_set.py "Spikformer v2.pdf" --tags "脉冲神经网络 SNN,Transformer,架构创新"
```

`check_presets.py` is a **read-only helper** — it never writes. Use it as part of step 2 (propose) to flag any candidate that isn't in the preset list, so the user can decide whether to create a new tag or pick a preset.

## The full set of preset tags

See `references/tag-taxonomy.md` for the current list, the rough meaning of each (where it's not obvious from the name), and the **disambiguation rules** for similar-looking tags (e.g. `Transformer` vs `架构创新`).

## Research-process guidance

Tagging is how the user remembers. A coherent tag scheme after a project is worth more than 5 random tags mid-stream. Specifically:
- **Mid-project**: don't tag every artifact. Tag milestones (Phase 0 done, Phase 2 done).
- **End of project**: do a sweep. Update the brief direction paper, the related-work papers, and any new artifacts.
- **Cross-project**: when a paper becomes relevant to a NEW project, add the new project's tag — don't remove old tags.

If the user has many papers, the tag-sweep can be a 5-minute task. Don't drag it out.
