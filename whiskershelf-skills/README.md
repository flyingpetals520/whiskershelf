# WhiskerShelf Skills

Five skills that turn Claude Code into a research collaborator for a WhiskerShelf-generated brief project. They are auto-loaded by Claude Code when it starts in a `whiskershelf-brief-*` project directory (the Idea Spark "Generate CC Project" feature copies this whole tree into `.claude/skills/`).

## What's in each skill

```
whiskershelf-skills/
├── README.md                              ← you are here
│
├── whiskershelf-brief/                    # Load the brief.md as a task spec
│   ├── SKILL.md
│   ├── references/
│   │   ├── brief-schema.md                # exact structure of brief.md
│   │   └── research-workflow.md           # 4 common research patterns
│   ├── scripts/
│   │   └── parse_brief.py                 # structure-extract the brief
│   └── examples/
│       └── sample_brief.md
│
├── whiskershelf-search/                   # Query the LOCAL WhiskerShelf library
│   ├── SKILL.md
│   ├── references/
│   │   ├── api-endpoints.md               # full Agent API reference
│   │   └── search-tips.md
│   ├── scripts/
│   │   ├── ws_common.py                   # shared HTTP helper
│   │   ├── ws_search.py / ws_search.sh    # substring search
│   │   ├── ws_papers.py / ws_papers.sh    # list everything (--tag, --name-only)
│   │   ├── ws_detail.py / ws_detail.sh    # one paper's full record
│   │   ├── ws_tags_get.py / ws_tags_get.sh# read a paper's tags
│   │   └── ws.ps1                         # PowerShell dispatcher for Windows
│   └── examples/
│       └── queries.md
│
├── whiskershelf-web-search/               # Query the OPEN literature
│   ├── SKILL.md
│   ├── references/
│   │   ├── arxiv-categories.md            # cs.LG, cs.NE, etc.
│   │   ├── venues.md                      # arxiv, S2, OpenReview, PwC, Scholar
│   │   └── query-templates.md             # starter queries by field
│   ├── scripts/
│   │   ├── arxiv_search.py / arxiv_search.sh
│   │   ├── s2_search.py / s2_search.sh    # Semantic Scholar
│   │   └── fetch_paper.py / fetch_paper.sh# by arxiv id or DOI
│   └── examples/
│       └── queries.md
│
├── whiskershelf-tag/                      # Read/write paper tags (gated)
│   ├── SKILL.md
│   ├── references/
│   │   ├── tag-taxonomy.md                # the 27 presets + disambiguation
│   │   └── tag-rules.md
│   ├── scripts/
│   │   ├── ws_common.py
│   │   ├── ws_tags_get.py / ws_tags_get.sh
│   │   ├── ws_tags_set.py / ws_tags_set.sh# GATED write; has --dry-run
│   │   └── check_presets.py / check_presets.sh
│   └── examples/
│       └── session.md
│
└── whiskershelf-subagents/                # Parallel subagent dispatch
    ├── SKILL.md
    ├── references/
    │   ├── subagent-templates.md          # copy-paste Task() prompts
    │   └── dispatch-patterns.md           # 4 dispatch patterns + synthesis template
    ├── scripts/
    │   └── dispatch_pipeline.py           # build a 5-stage dispatch plan from a brief
    └── examples/
        └── parallel-tasks.md
```

## The combined workflow

1. CC starts → loads `whiskershelf-brief` from this directory.
2. User picks a direction → CC uses `parse_brief.py` to extract it, then `whiskershelf-search` / `whiskershelf-web-search` for context.
3. If the user wants depth → CC uses `whiskershelf-subagents` (and the `dispatch_pipeline.py` helper) to spawn 4–7 parallel subagents, then synthesizes.
4. During execution, CC may use `whiskershelf-tag` (gated) to organize new artifacts.
5. At the end, CC writes up findings and tags relevant papers.

## Conventions

- **Stdlib-only** Python (no pip install required). The CLIs in `scripts/` work in any Python 3.8+ env.
- **Cross-platform** — every `.sh` script has a Python counterpart (`.py`) for Windows users who don't have bash.
- **Gated writes** — only `whiskershelf-tag` writes to user state, and the SKILL.md enforces a confirm-before-write protocol.
- **Server-availability** — the local-search and tag scripts require the WhiskerShelf app to be running on `127.0.0.1:8080`. The web-search scripts do not.
- **Reuse the same helper across skills** — `ws_common.py` is duplicated per skill so each can evolve independently.

## When the skills are loaded

WhiskerShelf's `app.py` does the heavy lifting at idea-spark export time:

```python
# from app.py:649 (build_cc_project)
if SKILLS_DIR.exists():
    copytree(SKILLS_DIR, target / ".claude" / "skills")
```

So the path inside a generated project is `.claude/skills/whiskershelf-*/` — same as in this top-level directory. If you update a skill here, the next "Generate CC Project" picks it up automatically.
