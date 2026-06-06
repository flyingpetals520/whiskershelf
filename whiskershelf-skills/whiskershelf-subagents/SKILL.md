---
name: whiskershelf-subagents
description: Delegate parallel exploration to subagents for deep cross-domain analysis and a fully-formed work plan. Use when the user asks for "a complete plan", "explore in depth", or "give me an actionable roadmap" — situations where a single-agent pass is too shallow.
---

# Whiskershelf Subagents

For deep, multi-angle exploration, **delegate to subagents in parallel**. You have a `Task` tool that spawns fresh subagents with isolated context. Each one comes back with a focused report. Your job: dispatch the right agents, then synthesize their findings into a single, actionable plan.

This is for when the user wants **depth, not speed**. If the brief already gives a clear direction, just execute it. Use this skill when the user signals they want comprehensive analysis before committing.

## When to use

- The user says: "give me a complete plan", "explore this thoroughly", "do your homework", "what's the full landscape", "I want a roadmap"
- The brief has multiple candidate directions and the user wants a recommendation based on deep investigation
- A direction is high-stakes (long-running, big investment) and warrants upfront diligence
- The user explicitly says "I want you to think before coding" or "show me the trade-offs"
- The brief is in a cross-domain area where the user is not a domain expert and wants a thoroughness check

**Don't use** when:
- The direction is obvious and the user wants to start coding immediately
- The user has already decided and just wants execution
- The work is a simple bug fix or small feature
- The brief has < 2 papers (subagents need multiple angles to chew on)

## 5-stage subagent pipeline

Each stage's subagents are **independent** — dispatch them in **one parallel batch** for stages 1–3, then synthesize. Stages 4–5 are sequential because they need earlier outputs.

A dispatch helper is in `scripts/dispatch_pipeline.py` — it prints a one-line-per-subagent summary you can paste into a `Task` call, or use as a checklist. The helper never actually spawns anything; you still control the `Task` tool.

### Stage 1: Per-paper deep dive (parallel, 2–4 subagents)

Spawn one subagent per paper from `selected-papers.json` (or the chosen direction's papers). Each subagent's task:
- Read the paper's abstract (use `whiskershelf-search` Skill to fetch via `GET /api/agent/papers/{name}`)
- Identify the **3–5 key technical mechanisms** (not surface features — actual algorithmic steps)
- Note: inputs, outputs, training data, compute, key hyperparameters, failure modes
- For each mechanism, answer: "What is the *minimum* I'd need to re-implement this?"
- Output: a tight 1-page technical summary

**Limit: 2–4 papers.** More papers = more confusion, not more insight.

### Stage 2: Cross-domain analysis (parallel, 2–3 subagents)

Spawn 2–3 subagents to explore different angles of the same research direction:
- **Subagent A — Method transfer**: Take the core mechanism from paper X. What changes are needed to apply it to paper Y's task? What's the *first concrete experiment*?
- **Subagent B — Counterfactual / Risk**: Assume we implement the direction. What would make it fail? What's the most likely negative result? Are there hidden assumptions?
- **Subagent C — Adjacent opportunities**: While implementing direction 1, what other 2–3 directions from the brief become newly feasible? (Misdirection often unlocks — note the side doors.)

Run A, B, C in parallel.

### Stage 3: External validation (1 subagent, optional but recommended)

Spawn 1 subagent to **validate against the open literature** using the `whiskershelf-web-search` Skill. This subagent should:
- Search arxiv / Semantic Scholar for the specific method + application domain
- Find the **3–5 most-cited recent papers** in this exact intersection
- Note: does anyone already do this? If so, how? What's the delta?
- Output: a 1-paragraph "competitive landscape" summary

### Stage 4: Synthesis (you, the main agent)

After stages 1–3 return, you produce a unified `## Execution Plan` with these sections (a template is in `references/dispatch-patterns.md`):

```
### Phase 0: Setup (Day 0-1)
- [ ] Concrete setup steps (e.g., dataset download, env config, baseline code clone)

### Phase 1: Minimum viable reproduction (Day 1-3)
- [ ] Re-implement the *simplest* version of paper X's core method
- [ ] Run on a toy dataset
- [ ] Verify it works (sanity check)

### Phase 2: Transfer to target domain (Day 3-7)
- [ ] Adapt method to paper Y's task
- [ ] Define 2–3 evaluation metrics
- [ ] Run first real experiment

### Phase 3: Iteration (Day 7-14)
- [ ] Analyze Phase 2 results
- [ ] Address top 2 failure modes (from Subagent B)
- [ ] Re-run, compare to baseline

### Phase 4: Writeup (Day 14+)
- [ ] Draft findings (even if partial)
- [ ] Update the user's WhiskerShelf notes for this paper
- [ ] Tag the project with relevant tags via `whiskershelf-tag`
```

### Stage 5: User sign-off

Present the plan. **Don't start coding** until the user approves or adjusts a phase. The plan is a contract — phases can be reordered or dropped, but starting silently is the failure mode this skill exists to prevent.

## Subagent invocation pattern

For each subagent, give it:
- A **specific, scoped task** (one question or one report, not "do everything")
- The **inputs it needs** (paper names, abstract snippets, relevant URL)
- The **output format** (e.g., "1 page, sections: Mechanism, Reproducibility, Risks")
- A reminder to **not call back to you** — return its report as a single message and stop

Example dispatch (pseudo-code):
```
Task(
  subagent_type: "general-purpose",
  prompt: "Read brief.md. Focus on the FIRST research direction. Produce a 1-page report with: (1) the core mechanism in 3-5 sentences, (2) what it would take to re-implement, (3) the most likely failure mode. Return the report and stop."
)
```

Concrete, copy-pasteable templates for each subagent type are in `references/subagent-templates.md`.

## When the plan should be re-dispatched

If the user comes back after a few days and the situation has changed (a new paper appeared, a key result came back negative), you don't need to re-run the full pipeline. Instead:
- Re-run only Stage 2 (cross-domain analysis) if the new info is methodological.
- Re-run only Stage 3 (external validation) if a year has passed and you want fresh SOTA.
- Skip stages when nothing has changed.

## Tone

You are a **research lead**, not a code monkey. Be honest about uncertainty — if the literature is thin or the direction is risky, say so. A plan that admits "this might not work, here's why" is more useful than one that hides the risks. The user can act on honesty; they can't act on false confidence.

See `examples/parallel-tasks.md` for a worked example of a 4-subagent dispatch session.
