# Dispatch Patterns

How to actually call the `Task` tool for a 5-stage pipeline, including the exact prompt shapes and the synthesis template that the lead fills in after stages 1–3.

## Pattern: "I want a complete plan"

User: "I want a roadmap. Think this through before we start."

**Dispatch (one parallel batch — three `Task` calls in the same message):**

1. **Stage 1** — one `Task` per paper (2–4 tasks). Use the template from `subagent-templates.md` § Stage 1A.
2. **Stage 2** — three `Task` calls (2A, 2B, 2C). All in parallel with stage 1.
3. **Stage 3** — one `Task` call (external validation). In parallel with stages 1–2.

This is **6–8 `Task` calls in a single message**, all parallel. Each returns its own report.

**Synthesize (in the main agent, after all tasks return):**

Use the template below. Fill in each section from the corresponding subagent's report. If any subagent's report is missing a section, either re-dispatch (preferred) or note the gap.

```markdown
# Execution Plan: <direction title>

> Source: brief.md
> Built from: <N> per-paper reports, 3 cross-domain reports, 1 external-validation report.
> Confidence: <HIGH / MEDIUM / LOW — based on the Stage 2B risk report and the Stage 3 verdict>

## TL;DR (1 paragraph)
<one paragraph: what we're doing, why, what's the expected payoff, what's the biggest risk>

## Phase 0: Setup (Day 0-1)
- [ ] <step from Stage 1A's "Re-implementation Skeleton" — only the env-setup portion>
- [ ] <dataset download — from Stage 1A's "Inputs / Outputs">
- [ ] <baseline code clone — if any subagent mentioned a reference repo>

## Phase 1: Minimum viable reproduction (Day 1-3)
- [ ] <the simplest version of paper X's core method, from Stage 1A>
- [ ] <run on a toy dataset — from Stage 2A's "First Concrete Experiment">
- [ ] <sanity check: loss decreases, metric improves over random>
- [ ] **Exit criterion**: a 1-page plot + table; loss < N, metric > M.

## Phase 2: Transfer to target domain (Day 3-7)
- [ ] <adapt method to paper Y's task, from Stage 2A>
- [ ] <define 2–3 evaluation metrics, from Stage 2A>
- [ ] <run first real experiment>
- [ ] **Exit criterion**: results table with at least one metric that beats the baseline from paper Y.

## Phase 3: Iteration (Day 7-14)
- [ ] <analyze Phase 2 results; what went wrong?>
- [ ] <address top 2 failure modes, prioritized by Stage 2B>
- [ ] <re-run, compare to baseline>
- [ ] **Exit criterion**: improvement over baseline on at least 1 metric, OR a clean negative result with an explanation.

## Phase 4: Writeup (Day 14+)
- [ ] <draft findings — even if partial>
- [ ] <update WhiskerShelf notes via whiskershelf-search + manual edit>
- [ ] <tag relevant papers via whiskershelf-tag>

## What could derail this
<paste Stage 2B's "Strongest Assumption" + "Most Likely Negative Result" + "What Would Make You Walk Away" — verbatim or summarized>

## Side doors to consider mid-flight
<paste Stage 2C's 2–3 "Side Door" entries — these become re-dispatch triggers if the user signals interest>

## External landscape
<paste Stage 3's "Closest Existing Work" + verdict>

## Citations to add
<paste Stage 3's "Citations to Add" — ready to insert into brief.md or the working notes>
```

**Present to the user (Stage 5).** Don't code. Wait for approval.

## Pattern: "I just want risk analysis"

User: "I'm worried this might not work. Poke holes in it before I commit."

**Dispatch:** Stage 1 (one paper deep dive, the most relevant one) + Stage 2B (risk only) in parallel. Skip 2A, 2C, 3.

**Synthesize:** A 1-page risk brief with the top 3 failure modes, ranked, and the "what would make you walk away" trigger. Present, get user's call, then either proceed with the full pipeline or pivot.

## Pattern: "Is this novel?"

User: "Has anyone already done this? Don't waste my time."

**Dispatch:** Stage 3 (external validation) only. Wait for the GREEN/YELLOW/RED verdict.

- GREEN: proceed with full pipeline.
- YELLOW: do Stage 2A to design a clear differentiation, then proceed.
- RED: tell the user, suggest pivoting to a related-but-unclaimed direction.

## Pattern: "I'm starting a new phase"

User: "We finished Phase 2. What's next?"

No new subagents. Look at the existing plan. Suggest Phase 3. If the user wants to **pivot** mid-execution, re-run Stage 2B (risk) and Stage 3 (external validation) for the new direction, then re-synthesize.

## Anti-patterns

- **Dispatching a single mega-subagent** that does everything. Each subagent must have a single, scoped task. "Do the whole plan" is what *you* (the lead) do, after gathering reports.
- **Sequential dispatch when parallel is possible.** Stages 1, 2, 3 are independent; always fire them in the same message.
- **Skipping Stage 5.** No code before the user approves the plan.
- **Ignoring Stage 2B's recommendation.** If the risk subagent says "this will fail", you can't write that out of the plan. Surface the conflict to the user.
- **Re-running the full pipeline when one stage would do.** See "When the plan should be re-dispatched" in SKILL.md.

## Time budgets for the lead

A 5-stage pipeline with 8 subagents typically takes 3–10 minutes wall-clock (subagents are fast) and produces 8–15 pages of reports. The lead's synthesis is another 5–10 minutes. The user should not be left waiting silently — narrate between dispatches: "Spawning 8 parallel subagents now; will report back in a few minutes."
