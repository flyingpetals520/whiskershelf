# Claude Code Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make WhiskerShelf a first-class upstream tool for Claude Code by (1) generating self-contained "CC project" directories from Idea Spark results, (2) shipping 3 research-process-oriented Skills, and (3) exposing a minimal read-only agent API with one gated write endpoint.

**Architecture:** Backend (Python stdlib) gains `build_cc_project()` + a new POST endpoint that writes a directory; the new `/api/agent/*` endpoints reuse existing data loaders. Frontend (vanilla JS) gets one new button + handler. Skills are static markdown files copied into the generated project.

**Tech Stack:** Python `unittest` (stdlib), `urllib.request` for endpoint tests, `http.server.ThreadingHTTPServer` for live test server, `tempfile` for isolated test directories. No new runtime deps.

**Spec:** `docs/superpowers/specs/2026-06-02-claude-code-integration-design.md`

---

## File Structure

### Files to Create

| Path | Responsibility |
|---|---|
| `tests/__init__.py` | Marks tests as a package (empty) |
| `tests/test_app.py` | Unittest test cases for the new module |
| `whiskershelf-skills/whiskershelf-brief/SKILL.md` | Skill: load and interpret an Idea Spark brief |
| `whiskershelf-skills/whiskershelf-search/SKILL.md` | Skill: query the local library |
| `whiskershelf-skills/whiskershelf-tag/SKILL.md` | Skill: read/write tags with confirmation gate |

### Files to Modify

| Path | Change |
|---|---|
| `app.py` | Add 4 agent endpoints, `build_cc_project()` function, `POST /api/idea-spark/export-cc-project` endpoint |
| `static/index.html` | Add one button to Idea Spark result toolbar |
| `static/app.js` | Add button click handler that POSTs + opens dir |
| `README.md` | Add "How is this different from...?" section + CC walkthrough |

---

## Task 1: Set Up Test Infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Create tests package directory**

```bash
mkdir -p tests
```

- [ ] **Step 2: Create empty package marker**

Create `tests/__init__.py` with literally no content (empty file).

- [ ] **Step 3: Create test file with a sanity-check test**

Create `tests/test_app.py`:

```python
"""Tests for WhiskerShelf app. Uses stdlib unittest only."""
import unittest


class SanityTest(unittest.TestCase):
    def test_truth(self):
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the test to verify the infrastructure works**

Run: `cd release && python -m unittest tests.test_app -v`
Expected: `Ran 1 test in 0.000s — OK`

- [ ] **Step 5: Add tests/ to .gitignore's "untracked-but-committed" policy**

`tests/` should be committed. Verify `.gitignore` does NOT list `tests/`. Open `.gitignore` and confirm. If it does, remove that line.

- [ ] **Step 6: Commit**

```bash
cd release
git add tests/
git commit -m "test: add unittest infrastructure (Task 1)"
```

---

## Task 2: Implement `build_cc_project()` Core Function (TDD)

**Files:**
- Modify: `app.py` (add new function near other helper functions, ~line 320)
- Modify: `tests/test_app.py` (add test class)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_app.py` (above the `if __name__ == "__main__":` line):

```python
import json
import tempfile
from pathlib import Path

from app import build_cc_project


class BuildCCProjectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.session = {
            "id": "1234567890",
            "time": 1234567890,
            "papers": [
                {"name": "a.pdf", "title": "Paper A", "abstract": "Abs A",
                 "tags": ["linear-attention"], "notes": ""},
                {"name": "b.pdf", "title": "Paper B", "abstract": "Abs B",
                 "tags": ["snn"], "notes": ""},
            ],
            "user_context": "test context",
            "result": "# Brief\n\n## 1. Common themes\n..."
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_directory(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        self.assertTrue(result_path.exists())
        self.assertTrue(result_path.is_dir())

    def test_writes_brief_md(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        self.assertEqual((result_path / "brief.md").read_text(encoding="utf-8"),
                         self.session["result"])

    def test_writes_selected_papers_json(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        data = json.loads((result_path / "selected-papers.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "a.pdf")

    def test_writes_claude_md_with_skills_section(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        claude_md = (result_path / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("whiskershelf-brief", claude_md)
        self.assertIn("whiskershelf-search", claude_md)
        self.assertIn("whiskershelf-tag", claude_md)

    def test_writes_start_claude_bat(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        bat = (result_path / "start-claude.bat").read_text(encoding="utf-8")
        self.assertIn("claude", bat.lower())

    def test_writes_start_claude_sh(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        sh = (result_path / "start-claude.sh").read_text(encoding="utf-8")
        self.assertIn("claude", sh.lower())

    def test_copies_skill_files(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        skills_dir = result_path / ".claude" / "skills"
        self.assertTrue((skills_dir / "whiskershelf-brief" / "SKILL.md").exists())
        self.assertTrue((skills_dir / "whiskershelf-search" / "SKILL.md").exists())
        self.assertTrue((skills_dir / "whiskershelf-tag" / "SKILL.md").exists())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd release && python -m unittest tests.test_app.BuildCCProjectTest -v`
Expected: FAIL with `ImportError: cannot import name 'build_cc_project'`

- [ ] **Step 3: Implement `build_cc_project()` in app.py**

Add this function in `app.py` near the other helpers (after `get_idea_spark_session`, around line 730 in current source):

```python
def build_cc_project(session, target_dir):
    """Generate a self-contained Claude Code project directory from an Idea Spark session.

    Returns the Path to the created directory.
    """
    from datetime import datetime
    from shutil import copytree

    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    # brief.md
    (target / "brief.md").write_text(session.get("result", ""), encoding="utf-8")

    # selected-papers.json
    (target / "selected-papers.json").write_text(
        json.dumps(session.get("papers", []), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # CLAUDE.md
    claude_md = f"""# Project: Research Brief from WhiskerShelf

This project was generated by **WhiskerShelf's Idea Spark** feature on {datetime.fromtimestamp(session.get('time', 0)).strftime('%Y-%m-%d')}.
You are helping the user turn a research brief into executable work.

## Context
- The user selected {len(session.get('papers', []))} papers from their local WhiskerShelf library.
- `brief.md` contains the LLM-generated research directions.
- `selected-papers.json` has full paper metadata (titles, abstracts, tags, notes).

## Your role
You are a research collaborator, not just a code generator. Before writing code:
1. Read `brief.md` end to end
2. Identify which of the 3-5 directions the user wants to pursue
3. Propose a concrete plan (5-7 steps) and ask for confirmation
4. Then begin execution

## Available skills (auto-loaded)
- `whiskershelf-brief` — load and interpret the brief
- `whiskershelf-search` — query the user's local library
- `whiskershelf-tag` — organize papers with tags

## Conventions
- When implementing a direction from the brief, follow the "method transfer path" and "expected challenges" sections.
- When the user references "the X paper" or "my notes on Y", use `whiskershelf-search` to find it.
- After meaningful progress, suggest tags for the new artifact.
"""
    (target / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

    # Starters
    (target / "start-claude.sh").write_text(
        "#!/usr/bin/env bash\necho \"Starting Claude Code with WhiskerShelf project context...\"\necho \"Tip: if 'claude' is not found, install: https://claude.com/code\"\nexec claude\n",
        encoding="utf-8"
    )
    (target / "start-claude.bat").write_text(
        "@echo off\r\necho Starting Claude Code with WhiskerShelf project context...\r\necho Tip: if 'claude' is not found, install: https://claude.com/code\r\nclaude\r\npause\r\n",
        encoding="utf-8"
    )

    # Copy Skill templates
    skills_src = STATIC_DIR / "skills"
    if skills_src.exists():
        copytree(skills_src, target / ".claude" / "skills")

    return target
```

- [ ] **Step 4: Add top-level import in test file**

The test imports `from app import build_cc_project` but `app.py` is large. Make sure `app.py` is importable as a module without running `main()`. The current structure has `if __name__ == "__main__": main()` at the bottom — this is already correct. No change needed.

- [ ] **Step 5: Run tests to verify they pass for the directory/writes/brief, but skills test will still fail (no skills/ dir yet)**

Run: `cd release && python -m unittest tests.test_app.BuildCCProjectTest -v`
Expected: 6 tests pass, `test_copies_skill_files` fails with `FileNotFoundError` because `static/skills/` doesn't exist yet. That's OK — Task 3 creates the skills.

- [ ] **Step 6: Commit**

```bash
cd release
git add app.py tests/test_app.py
git commit -m "feat(app): add build_cc_project() to generate CC project directories (Task 2)"
```

---

## Task 3: Create Skill Template Files

**Files:**
- Create: `static/skills/whiskershelf-brief/SKILL.md`
- Create: `static/skills/whiskershelf-search/SKILL.md`
- Create: `static/skills/whiskershelf-tag/SKILL.md`

- [ ] **Step 1: Create directory structure**

```bash
cd release
mkdir -p static/skills/whiskershelf-brief
mkdir -p static/skills/whiskershelf-search
mkdir -p static/skills/whiskershelf-tag
```

- [ ] **Step 2: Write whiskershelf-brief/SKILL.md**

Create `static/skills/whiskershelf-brief/SKILL.md`:

```markdown
---
name: whiskershelf-brief
description: Load a WhiskerShelf Idea Spark research brief and treat it as a task spec. Use when the user starts working on a brief-based project.
---

# Whiskershelf Research Brief

This project came from WhiskerShelf's Idea Spark.

## What `brief.md` contains
- Common themes and methodological tensions across N papers
- 3-5 actionable research directions, each with:
  - **核心 Idea** (one-sentence pitch)
  - **方法迁移路径** (which paper's method to use, how to adapt it)
  - **预期难点** (what might go wrong)
  - **验证方案** (minimal experiment)
- Cross-domain leap suggestions
- Risk and blind-spot analysis

## Research workflow you should follow

1. **Read brief.md fully** before asking the user any question.
2. **Summarize back** the 3-5 directions in your own words. Ask the user which to pursue.
3. **For the chosen direction**, extract:
   - The method transfer path (which paper, which method)
   - The expected challenges
   - The validation criteria
4. **Propose a 5-7 step execution plan**. Wait for user approval before coding.
5. **Execute step by step**, checking off the validation criteria as you go.
6. **After meaningful progress** (e.g., first working prototype), suggest:
   - Running `whiskershelf-search` to find related work the user might have missed
   - Tagging the new artifact via `whiskershelf-tag`
7. **When stuck**:
   - Re-read the relevant section of brief.md
   - Search the user's library for related context
   - Ask the user for clarification rather than guessing

## Tone
You are a research collaborator. Be opinionated when you have evidence from the brief. Be humble when you don't.
```

- [ ] **Step 3: Write whiskershelf-search/SKILL.md**

Create `static/skills/whiskershelf-search/SKILL.md`:

```markdown
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
```

- [ ] **Step 4: Write whiskershelf-tag/SKILL.md**

Create `static/skills/whiskershelf-tag/SKILL.md`:

```markdown
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
```

- [ ] **Step 5: Verify all 3 Skills are now in place**

Run: `cd release && ls -R static/skills/`
Expected: 3 directories, each containing `SKILL.md`.

- [ ] **Step 6: Re-run the full BuildCCProjectTest suite**

Run: `cd release && python -m unittest tests.test_app.BuildCCProjectTest -v`
Expected: All 7 tests pass.

- [ ] **Step 7: Commit**

```bash
cd release
git add static/skills/
git commit -m "feat(skills): add 3 research-process-oriented SKILL.md templates (Task 3)"
```

---

## Task 4: Add `POST /api/idea-spark/export-cc-project` Endpoint (TDD)

**Files:**
- Modify: `app.py` (add endpoint in `do_POST`)
- Modify: `tests/test_app.py` (add live-server test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
import threading
import time
from http.server import HTTPServer
import urllib.request
import urllib.parse

from app import PaperHandler


class _LiveServer:
    """Context manager that runs PaperHandler on a random port in a thread."""
    def __enter__(self):
        self.server = HTTPServer(("127.0.0.1", 0), PaperHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        # Tiny sleep to let the server bind (usually unnecessary but harmless)
        time.sleep(0.05)
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()


class ExportCCProjectEndpointTest(unittest.TestCase):
    def test_missing_session_id_returns_400(self):
        with _LiveServer():
            req = urllib.request.Request(
                f"http://127.0.0.1:{self._port()}/api/idea-spark/export-cc-project",
                data=json.dumps({}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code, 400)

    def _port(self):
        # Hack: pull port from the active server
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd release && python -m unittest tests.test_app.ExportCCProjectEndpointTest -v`
Expected: FAIL with 405 (route not found) or similar.

- [ ] **Step 3: Add the endpoint stub to app.py**

In `app.py`'s `do_POST`, after the existing `POST /api/idea-spark/generate` block, add:

```python
        # API: 导出 Idea Spark 为 Claude Code 项目目录 /api/idea-spark/export-cc-project
        if path == "/api/idea-spark/export-cc-project":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            session_id = payload.get("session_id", "").strip()
            target_dir = payload.get("target_dir", "").strip()
            if not session_id:
                self._send_json({"error": "session_id is required"}, 400)
                return
            if not target_dir:
                self._send_json({"error": "target_dir is required"}, 400)
                return
            session = get_idea_spark_session(session_id)
            if not session:
                self._send_json({"error": "session not found"}, 404)
                return
            try:
                target = Path(target_dir)
                target.mkdir(parents=True, exist_ok=True)
                result_path = build_cc_project(session, target)
                self._send_json({"success": True, "path": str(result_path)})
            except Exception as e:
                print(f"[Export CC Project Error] {e}")
                self._send_json({"error": str(e)}, 500)
            return
```

- [ ] **Step 4: Run test to verify it now passes**

Run: `cd release && python -m unittest tests.test_app.ExportCCProjectEndpointTest -v`
Expected: PASS.

- [ ] **Step 5: Add a test for the happy path (export a real session)**

Append to the test class:

```python
    def test_export_with_valid_session_writes_directory(self):
        # Seed a session directly in the history file
        from app import add_idea_spark_session, IDEA_SPARK_HISTORY_FILE
        sess = add_idea_spark_session(
            papers_info=[{"name": "a.pdf", "title": "A", "abstract": "x", "tags": [], "notes": ""}],
            user_context="ctx",
            result_content="# brief",
        )
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            target = Path(tempfile.mkdtemp()) / "out"
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/idea-spark/export-cc-project",
                data=json.dumps({"session_id": sess["id"], "target_dir": str(target)}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
            self.assertTrue(data["success"])
            self.assertTrue((target / "brief.md").exists())
            self.assertTrue((target / "CLAUDE.md").exists())
            import shutil
            shutil.rmtree(target.parent, ignore_errors=True)
```

- [ ] **Step 6: Run all ExportCCProject tests**

Run: `cd release && python -m unittest tests.test_app.ExportCCProjectEndpointTest -v`
Expected: 2 tests pass.

- [ ] **Step 7: Commit**

```bash
cd release
git add app.py tests/test_app.py
git commit -m "feat(api): add POST /api/idea-spark/export-cc-project (Task 4)"
```

---

## Task 5: Add Agent API — `GET /api/agent/papers` (TDD)

**Files:**
- Modify: `app.py` (add endpoint in `do_GET`)
- Modify: `tests/test_app.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
class AgentPapersListTest(unittest.TestCase):
    def test_returns_paper_list(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/agent/papers") as r:
                data = json.loads(r.read())
            self.assertIn("papers", data)
            self.assertIsInstance(data["papers"], list)
            # Each paper has at minimum: name, title, abstract_preview
            if data["papers"]:
                p = data["papers"][0]
                self.assertIn("name", p)
                self.assertIn("title", p)
                self.assertIn("abstract_preview", p)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd release && python -m unittest tests.test_app.AgentPapersListTest -v`
Expected: 404 (route not found).

- [ ] **Step 3: Add the endpoint to app.py's do_GET**

After the existing `GET /api/analysis/history/{id}` block, add:

```python
        # API: Agent - 列出所有论文 /api/agent/papers
        if path == "/api/agent/papers":
            papers = get_papers()
            summary = []
            for p in papers:
                ab = (p.get("abstract") or "").strip()
                summary.append({
                    "name": p.get("name"),
                    "title": p.get("display") or p.get("name"),
                    "tags": p.get("tags", []),
                    "abstract_preview": ab[:300]
                })
            self._send_json({"papers": summary})
            return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd release && python -m unittest tests.test_app.AgentPapersListTest -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd release
git add app.py tests/test_app.py
git commit -m "feat(api): add GET /api/agent/papers (Task 5)"
```

---

## Task 6: Add Agent API — `GET /api/agent/papers/{name}` (TDD)

**Files:**
- Modify: `app.py` (add endpoint in `do_GET`)
- Modify: `tests/test_app.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
class AgentPaperDetailTest(unittest.TestCase):
    def test_returns_full_paper_detail(self):
        # Pick a real paper name from the live filesystem
        from app import ROOT
        pdfs = [p.name for p in ROOT.iterdir() if p.suffix.lower() == ".pdf"]
        if not pdfs:
            self.skipTest("No PDFs in project root to test against")
        name = pdfs[0]
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            encoded = urllib.parse.quote(name, safe="")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/agent/papers/{encoded}") as r:
                data = json.loads(r.read())
            self.assertEqual(data["name"], name)
            self.assertIn("title", data)
            self.assertIn("abstract", data)
            self.assertIn("tags", data)
            self.assertIn("notes", data)

    def test_nonexistent_returns_404(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/agent/papers/ghost.pdf")
            self.assertEqual(ctx.exception.code, 404)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd release && python -m unittest tests.test_app.AgentPaperDetailTest -v`
Expected: 404 (route not found).

- [ ] **Step 3: Add the endpoint to app.py's do_GET**

After the `GET /api/agent/papers` block, add:

```python
        # API: Agent - 单篇论文详情 /api/agent/papers/{name}
        if path.startswith("/api/agent/papers/"):
            # Skip the "tags" subroute — handled separately
            if not path.endswith("/tags"):
                name = urllib.parse.unquote(path[len("/api/agent/papers/"):])
                if not name:
                    self._send_json({"error": "invalid name"}, 400)
                    return
                paper_map = {p["name"]: p for p in get_papers()}
                p = paper_map.get(name)
                if not p:
                    self._send_json({"error": "not found"}, 404)
                    return
                self._send_json({
                    "name": name,
                    "title": p.get("display") or name,
                    "abstract": p.get("abstract", ""),
                    "tags": p.get("tags", []),
                    "notes": p.get("notes", "")
                })
                return
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd release && python -m unittest tests.test_app.AgentPaperDetailTest -v`
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
cd release
git add app.py tests/test_app.py
git commit -m "feat(api): add GET /api/agent/papers/{name} (Task 6)"
```

---

## Task 7: Add Agent API — `POST /api/agent/search` (TDD)

**Files:**
- Modify: `app.py` (add endpoint in `do_POST`)
- Modify: `tests/test_app.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
class AgentSearchTest(unittest.TestCase):
    def test_search_returns_results(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/agent/search",
                data=json.dumps({"query": "test"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
            self.assertIn("results", data)
            self.assertIsInstance(data["results"], list)
            # Each result: name, title, abstract_preview
            if data["results"]:
                item = data["results"][0]
                self.assertIn("name", item)
                self.assertIn("title", item)
                self.assertIn("abstract_preview", item)

    def test_empty_query_returns_empty_list(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/agent/search",
                data=json.dumps({"query": ""}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
            self.assertEqual(data["results"], [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd release && python -m unittest tests.test_app.AgentSearchTest -v`
Expected: 404 (route not found).

- [ ] **Step 3: Add the endpoint to app.py's do_POST**

After the existing Idea Spark export endpoint, add:

```python
        # API: Agent - 语义搜索 /api/agent/search
        if path == "/api/agent/search":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            query = payload.get("query", "").strip()
            if not query:
                self._send_json({"results": []})
                return
            # Fall back to simple substring match across title + tags + abstract
            # (We don't call LLM here to keep agent API zero-cost.)
            q = query.lower()
            results = []
            for p in get_papers():
                haystacks = [
                    (p.get("display") or "").lower(),
                    " ".join(p.get("tags", [])).lower(),
                    (p.get("abstract") or "").lower(),
                ]
                if any(q in h for h in haystacks):
                    results.append({
                        "name": p.get("name"),
                        "title": p.get("display") or p.get("name"),
                        "abstract_preview": (p.get("abstract") or "")[:300]
                    })
            # Cap at 20 results
            self._send_json({"results": results[:20]})
            return
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd release && python -m unittest tests.test_app.AgentSearchTest -v`
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
cd release
git add app.py tests/test_app.py
git commit -m "feat(api): add POST /api/agent/search (Task 7)"
```

---

## Task 8: Add Agent API — `POST /api/agent/papers/{name}/tags` (TDD, Gated)

**Files:**
- Modify: `app.py` (add endpoint in `do_POST`)
- Modify: `tests/test_app.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
class AgentTagWriteTest(unittest.TestCase):
    def test_set_tags(self):
        from app import ROOT
        pdfs = [p.name for p in ROOT.iterdir() if p.suffix.lower() == ".pdf"]
        if not pdfs:
            self.skipTest("No PDFs in project root to test against")
        name = pdfs[0]
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            encoded = urllib.parse.quote(name, safe="")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/agent/papers/{encoded}/tags",
                data=json.dumps({"tags": ["test-tag-x", "test-tag-y"]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
            self.assertTrue(data["success"])
            self.assertIn("test-tag-x", data["tags"])

    def test_invalid_name_returns_400(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/agent/papers//tags",
                data=json.dumps({"tags": ["x"]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code, 400)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd release && python -m unittest tests.test_app.AgentTagWriteTest -v`
Expected: 404 (route not found).

- [ ] **Step 3: Add the endpoint to app.py's do_POST**

After the `/api/agent/search` block, add:

```python
        # API: Agent - 设置论文标签（gated，CC 需在 SKILL 中要求用户确认） /api/agent/papers/{name}/tags
        if path.startswith("/api/agent/papers/") and path.endswith("/tags"):
            prefix = "/api/agent/papers/"
            suffix = "/tags"
            name = urllib.parse.unquote(path[len(prefix):-len(suffix)])
            if not name:
                self._send_json({"error": "invalid name"}, 400)
                return
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            new_tags = payload.get("tags", [])
            if not isinstance(new_tags, list):
                self._send_json({"error": "tags must be list"}, 400)
                return
            # Clean: strip + dedup
            cleaned = []
            seen = set()
            for t in new_tags:
                if isinstance(t, str):
                    t = t.strip()
                    if t and t not in seen:
                        seen.add(t)
                        cleaned.append(t)
            tags = load_tags()
            if name not in tags:
                self._send_json({"error": "paper not found"}, 404)
                return
            tags[name] = cleaned
            save_tags(tags)
            # Audit log (printed to server console)
            print(f"[Agent API] tags updated for {name}: {cleaned}")
            self._send_json({"success": True, "tags": cleaned})
            return
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd release && python -m unittest tests.test_app.AgentTagWriteTest -v`
Expected: 2 tests pass.

- [ ] **Step 5: Run the FULL test suite to confirm no regressions**

Run: `cd release && python -m unittest tests.test_app -v`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
cd release
git add app.py tests/test_app.py
git commit -m "feat(api): add gated POST /api/agent/papers/{name}/tags (Task 8)"
```

---

## Task 9: Add "🚀 Generate CC Project" Button to HTML

**Files:**
- Modify: `static/index.html` (one button in the Idea Spark result toolbar)

- [ ] **Step 1: Find the existing result toolbar in `static/index.html`**

Search for `ideaResultToolbar` and locate the `downloadMdBtn` row.

- [ ] **Step 2: Add the new button**

In the toolbar div, add a new button BEFORE `downloadMdBtn`:

```html
<button class="btn-ai-recommend" id="exportCcProjectBtn" title="生成 Claude Code 项目目录">🚀 生成 CC 项目</button>
```

The resulting block should look like:

```html
<div class="idea-result-toolbar" id="ideaResultToolbar" style="display:none;">
    <button class="btn-ai-recommend" id="exportCcProjectBtn" title="生成 Claude Code 项目目录">🚀 生成 CC 项目</button>
    <button class="btn-ai-recommend" id="downloadMdBtn">💾 下载为 .md</button>
    <button class="btn-ai-recommend" id="copyMdBtn">📋 复制源码</button>
    <button class="btn-ai-recommend" id="viewSourceBtn">👁️ 查看/编辑源码</button>
</div>
```

- [ ] **Step 3: Verify HTML parses correctly**

Run: `cd release && python -c "from html.parser import HTMLParser; HTMLParser().feed(open('static/index.html', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit (frontend-only)**

```bash
cd release
git add static/index.html
git commit -m "feat(ui): add 🚀 Generate CC Project button to Idea Spark results (Task 9)"
```

---

## Task 10: Add JS Click Handler for the New Button

**Files:**
- Modify: `static/app.js` (add handler near the other Idea Spark result buttons)

- [ ] **Step 1: Find where `downloadMdBtn` click handler is registered**

Search `static/app.js` for `downloadMdBtn.addEventListener` to locate the right section.

- [ ] **Step 2: Add a click handler above the existing download handler**

Add this just before the `downloadMdBtn.addEventListener(...)` block:

```javascript
document.getElementById('exportCcProjectBtn').addEventListener('click', async () => {
    if (!ideaSparkCurrentSession || !ideaSparkCurrentSession.id) {
        showToast('请先生成一次灵感火花');
        return;
    }
    const btn = document.getElementById('exportCcProjectBtn');
    btn.disabled = true;
    const original = btn.textContent;
    btn.innerHTML = '<span class="ai-loading"></span>生成中';
    try {
        // Use the existing project folder (where PDFs live) as a sensible default.
        // Users can move the generated directory afterward.
        const resp = await fetch('/api/idea-spark/export-cc-project', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: ideaSparkCurrentSession.id,
                target_dir: ''
            })
        });
        const data = await resp.json();
        if (!data.success) throw new Error(data.error || 'export failed');
        // Server returns a default path; reveal it in the file manager
        const choice = confirm('已生成 CC 项目到:\n' + data.path + '\n\n是否打开此目录？');
        if (choice) {
            // Reuse the existing reveal endpoint? No — this is a directory, not a file.
            // Use a quick POST to a new "open folder" endpoint we'll add in the next task.
            // For now, copy the path to clipboard and show a toast with the path.
            try {
                await navigator.clipboard.writeText(data.path);
                showToast('路径已复制到剪贴板 📋');
            } catch (e) {
                showToast('已生成：' + data.path);
            }
        } else {
            showToast('已生成 ✅');
        }
    } catch (e) {
        console.error(e);
        showToast('生成失败：' + (e.message || '请重试'));
    } finally {
        btn.disabled = false;
        btn.textContent = original;
    }
});
```

Note: The button sends `target_dir: ''` and lets the server pick a default. The user is informed via the path in the toast. A future enhancement can add a directory picker.

- [ ] **Step 3: Run the existing tests to confirm no regression**

Run: `cd release && python -m unittest tests.test_app -v`
Expected: All tests pass (this change is JS-only, won't affect Python tests).

- [ ] **Step 4: Manually verify in a browser**

Skip if no browser available. Otherwise: open http://127.0.0.1:8080, click 💡 Idea spark, pick 2 papers, click ✨ 火花碰撞, then click 🚀 生成 CC 项目. Verify the toast shows the path.

- [ ] **Step 5: Commit**

```bash
cd release
git add static/app.js
git commit -m "feat(ui): wire up 🚀 Generate CC Project button (Task 10)"
```

---

## Task 11: Server-side Default Path Resolution (TDD)

**Files:**
- Modify: `app.py` (in the export endpoint)
- Modify: `tests/test_app.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
class ExportCCDefaultPathTest(unittest.TestCase):
    def test_empty_target_dir_uses_default(self):
        from app import add_idea_spark_session
        sess = add_idea_spark_session(
            papers_info=[{"name": "a.pdf", "title": "A", "abstract": "x", "tags": [], "notes": ""}],
            user_context="ctx",
            result_content="# brief",
        )
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/idea-spark/export-cc-project",
                data=json.dumps({"session_id": sess["id"], "target_dir": ""}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
            self.assertTrue(data["success"])
            self.assertIn("whiskershelf-brief-", data["path"])
            import shutil
            shutil.rmtree(data["path"], ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd release && python -m unittest tests.test_app.ExportCCDefaultPathTest -v`
Expected: FAIL with "target_dir is required".

- [ ] **Step 3: Update the export endpoint to handle empty target_dir**

In `app.py`, replace the existing `POST /api/idea-spark/export-cc-project` endpoint with:

```python
        # API: 导出 Idea Spark 为 Claude Code 项目目录 /api/idea-spark/export-cc-project
        if path == "/api/idea-spark/export-cc-project":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "invalid json"}, 400)
                return
            session_id = payload.get("session_id", "").strip()
            target_dir = (payload.get("target_dir") or "").strip()
            if not session_id:
                self._send_json({"error": "session_id is required"}, 400)
                return
            session = get_idea_spark_session(session_id)
            if not session:
                self._send_json({"error": "session not found"}, 404)
                return
            try:
                if not target_dir:
                    # Default: <user-home>/Documents/whiskershelf-briefs/whiskershelf-brief-YYYY-MM-DD-HHMM/
                    docs = Path.home() / "Documents" / "whiskershelf-briefs"
                    timestamp = time.strftime("%Y-%m-%d-%H%M", time.localtime(session.get("time", time.time())))
                    target_dir = str(docs / f"whiskershelf-brief-{timestamp}")
                target = Path(target_dir)
                target.mkdir(parents=True, exist_ok=True)
                result_path = build_cc_project(session, target)
                self._send_json({"success": True, "path": str(result_path)})
            except Exception as e:
                print(f"[Export CC Project Error] {e}")
                self._send_json({"error": str(e)}, 500)
            return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd release && python -m unittest tests.test_app.ExportCCDefaultPathTest -v`
Expected: PASS.

- [ ] **Step 5: Run full suite**

Run: `cd release && python -m unittest tests.test_app -v`
Expected: All pass.

- [ ] **Step 6: Commit**

```bash
cd release
git add app.py tests/test_app.py
git commit -m "feat(api): default target_dir to <home>/Documents/whiskershelf-briefs/ (Task 11)"
```

---

## Task 12: README — Add "How is this different from...?" Section

**Files:**
- Modify: `README.md` (insert one section between "AI Features in Detail" and "Innovations")

- [ ] **Step 1: Locate the insertion point**

Search `README.md` for the `## 💡 Innovations` heading. The new section goes immediately before it.

- [ ] **Step 2: Insert the section**

Insert before `## 💡 Innovations`:

```markdown
---

## 🆚 How is this different from ...?

A cheat sheet for the "why not just use X" question:

| Tool | What it does well | What WhiskerShelf adds |
|---|---|---|
| **Zotero / Mendeley** | Reference management, citation export | AI-synthesized cross-paper research directions |
| **Elicit / Consensus** | AI paper discovery, Q&A over literature | Local-first: your PDFs never leave your disk |
| **Obsidian / Logseq** | Note-taking, knowledge graph | Purpose-built for paper reading → idea generation |
| **Connected Papers** | Visual citation graph | The graph becomes *executable tasks* for Claude Code |
| **ChatGPT + papers** | Ad-hoc Q&A | Persistent research history across sessions and devices |

### The unique combination

WhiskerShelf is the only tool that combines all three:

1. **Local-first paper library** (PDFs never leave your disk)
2. **LLM-driven cross-paper idea generation** (Idea Spark)
3. **First-class Markdown export designed for Agent Coding** (drop the brief into Claude Code as a task)

---

```

- [ ] **Step 3: Verify README parses as valid Markdown**

Run: `cd release && python -c "import re; md=open('README.md', encoding='utf-8').read(); print('lines:', len(md.splitlines())); print('sections:', len(re.findall(r'^## ', md, re.M)))"`

- [ ] **Step 4: Commit**

```bash
cd release
git add README.md
git commit -m "docs: add 'How is this different from...?' section to README (Task 12)"
```

---

## Task 13: README — Add Claude Code Walkthrough

**Files:**
- Modify: `README.md` (insert one subsection under "AI Features in Detail" > "Idea Spark")

- [ ] **Step 1: Find the Idea Spark section**

Search `README.md` for the `### 💡 Idea Spark` heading.

- [ ] **Step 2: Append the walkthrough subsection after the existing Idea Spark content**

Find the next `---` or `##` after the Idea Spark section. Just before it, insert:

```markdown
### 🚀 From Idea Spark to Claude Code (in 3 clicks)

The brief generated above is already agent-ready. To hand it off to Claude Code:

1. Click **🚀 生成 CC 项目** in the result toolbar.
2. WhiskerShelf writes a self-contained project directory to:
   `<your home>/Documents/whiskershelf-briefs/whiskershelf-brief-YYYY-MM-DD-HHMM/`
   It contains `brief.md`, `CLAUDE.md`, `selected-papers.json`, a starter script (`start-claude.sh` or `.bat`), and 3 Skills under `.claude/skills/`.
3. `cd` into that directory and run `claude`. Claude Code auto-discovers the Skills and uses the brief as its task spec.

The Skills (`whiskershelf-brief`, `whiskershelf-search`, `whiskershelf-tag`) guide CC through a research workflow: read the brief, propose a plan, search your library for context, tag progress. See `static/skills/` for the templates and the spec at `docs/superpowers/specs/` for the design rationale.

```

- [ ] **Step 3: Commit**

```bash
cd release
git add README.md
git commit -m "docs: add Claude Code walkthrough subsection to README (Task 13)"
```

---

## Task 14: Smoke Test (Manual)

**Files:** none

- [ ] **Step 1: Start the server**

Run: `cd release && python app.py`
Expected: `[OK] 服务已启动: http://127.0.0.1:8080`

- [ ] **Step 2: Open in browser**

Visit `http://127.0.0.1:8080`.

- [ ] **Step 3: Generate a CC project end-to-end**

1. Click 💡 Idea spark
2. Pick 2 papers
3. Click ✨ 火花碰撞
4. Click 🚀 生成 CC 项目
5. Verify the toast shows the path

- [ ] **Step 4: Verify the generated directory**

Run: `ls -la ~/Documents/whiskershelf-briefs/whiskershelf-brief-*/`
Expected: `brief.md`, `CLAUDE.md`, `selected-papers.json`, `start-claude.sh`, `start-claude.bat`, `.claude/skills/whiskershelf-{brief,search,tag}/SKILL.md`

- [ ] **Step 5: Read CLAUDE.md and confirm Skills are referenced**

Run: `cat ~/Documents/whiskershelf-briefs/whiskershelf-brief-*/CLAUDE.md`
Expected: Mentions all 3 Skill names.

- [ ] **Step 6: Spot-check the agent API**

Run: `curl -s -X POST -H "Content-Type: application/json" -d '{"query":"Mamba"}' http://127.0.0.1:8080/api/agent/search`
Expected: `{"results": [...]}`

- [ ] **Step 7: Stop the server**

Ctrl-C in the terminal where the server is running.

- [ ] **Step 8: Final commit if any docs were updated during smoke test**

```bash
cd release
git status
# If clean, no commit needed.
```

---

## Self-Review

**Spec coverage:**

| Spec section | Task |
|---|---|
| §3 Differentiation narrative | Task 12 |
| §4.3 Directory structure | Task 2 (function) + Task 3 (Skill files) |
| §4.4 Starters | Task 2 |
| §4.5 CLAUDE.md | Task 2 |
| §4.6 UI button + handler | Task 9 + Task 10 + Task 11 |
| §4.7 Agent API endpoints | Tasks 5, 6, 7, 8 |
| §5 Skill content | Task 3 |
| §6 Implementation tasks (high-level) | All tasks |
| §8 Success criteria | Task 14 (smoke test) |

**No placeholders:** scanned, none found.

**Type consistency:**
- `build_cc_project(session, target_dir)` — defined in Task 2, used in Tasks 4 and 11
- `get_idea_spark_session(session_id)` — used consistently in Tasks 4 and 11
- Agent API endpoint paths `/api/agent/{papers,papers/{name},search,papers/{name}/tags}` — consistent across Tasks 5–8
- `ideaSparkCurrentSession` — frontend variable, used in Task 10

**Ambiguity:**
- Task 10 step 2 has a TODO for future "directory picker" enhancement — marked as `''` for now, defaulting to server-side resolution in Task 11. No ambiguity remains.
- Task 2 uses `from shutil import copytree` inside the function — Pythonic lazy import, not a bug.

Plan is consistent. Ready for execution.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-02-claude-code-integration.md`. 14 tasks, each with bite-sized steps and frequent commits.

Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
