# Subagent Prompt Templates

Copy-paste these into a `Task(subagent_type="general-purpose", prompt=...)` call. Each is a complete, scoped prompt — fill in the bracketed placeholders.

The common preamble (always include):

> You are one of several parallel subagents dispatched by a research lead. **Do not call back to the lead** — return your report as a single message and stop. Stay within your scope; do not attempt the other subagents' tasks.

---

## Stage 1A: Per-paper deep dive (use 2–4 of these in parallel)

For each paper in `selected-papers.json`, spawn one of these.

```
You are analyzing one paper from a WhiskerShelf Idea Spark brief.

Inputs:
  - Brief file:  ./brief.md
  - Paper name:  <PDF filename>
  - Your scope:  ONLY this paper. Do not analyze the others.

Steps:
  1. Fetch the paper's full abstract:
       GET http://127.0.0.1:8080/api/agent/papers/<url-encoded name>
     (Whiskershelf must be running. If the call fails, say so and stop.)
  2. Optionally skim the PDF directly for the Methods section.
  3. Produce a 1-page technical summary with EXACTLY these sections:
       ## Core Idea         (2–3 sentences, the elevator pitch)
       ## Key Mechanisms    (3–5 algorithmic steps, with names of the
                            specific operations, e.g. "LIF decay + surrogate gradient")
       ## Inputs / Outputs  (shapes, data types, dimensions if known)
       ## Hyperparameters   (the 3–5 that matter most)
       ## Failure Modes     (what the paper admits doesn't work or is brittle)
       ## Re-implementation Skeleton
                            (5–7 bullets: what files / what classes, in what order)
       ## Open Questions    (2–4 things you couldn't determine from the abstract)

Output format: a single Markdown document, no preamble. ≤ 1500 words.

Hard rules:
  - Do NOT speculate beyond what the abstract + paper support. If unsure, say so.
  - Do NOT touch the user's tags or notes (that's another skill).
  - Do NOT call any other subagent or skill.
  - When done, return the document. STOP.
```

If the paper is too dense for one read, note it in `## Open Questions` and recommend what to read first (specific section, e.g. "§3.2 of the PDF").

---

## Stage 2A: Method transfer

```
You are one of three parallel cross-domain subagents. Your angle: METHOD TRANSFER.

Inputs:
  - Brief file:  ./brief.md
  - Direction:   <e.g. "Direction 1: 把 RWKV-7 的状态演化机制迁移到脉冲域">
  - Source paper: <e.g. "RWKV-7 Goose with Expressive Dynamic State Evolution.pdf">
  - Target paper: <e.g. "Spikformer v2.pdf">
  - User constraints: <e.g. "single GPU, 4h compute, must work on N-Caltech-101">

Your job: design a concrete method-transfer pipeline. Don't write code;
write a *plan* that another agent (or human) could implement.

Output: a single Markdown document with:
  ## Mechanism in Source (3–5 sentences)
  ## What Transfers (and what doesn't)
  ## What Must Change for the Target Domain
         (5–10 specific algorithmic changes, ranked by risk)
  ## First Concrete Experiment
         (dataset, baseline, metrics, success criterion, estimated compute)
  ## Risks Specific to This Transfer
         (the 2–3 most likely failure modes for THIS combination, not generic ones)
  ## Minimal Reference Implementation Sketch
         (file-by-file, 5–8 bullets)

Hard rules:
  - No speculation about results; this is a planning document.
  - Stay scoped to this one method-transfer; do not analyze other directions.
  - Use `whiskershelf-web-search` if you need to confirm something the brief omits.
  - When done, return the document. STOP.
```

## Stage 2B: Counterfactual / Risk

```
You are the RISK subagent. Your job is to attack the chosen direction, not to
support it. The research lead wants honest negative results surfaced early.

Inputs:  same as 2A (direction, source, target, constraints).

Output: a single Markdown document with:
  ## Strongest Assumption in the Brief
         (the one thing that, if wrong, kills the direction)
  ## Most Likely Negative Result
         (the experiment that comes back with a worse number than baseline,
         and why)
  ## Hidden Costs
         (compute, data, hyperparameter sensitivity, engineering effort)
  ## What Would Make You Walk Away
         (2–3 specific signals from a 1-week pilot that would say "pivot")
  ## What You'd Try Before Giving Up
         (2–3 cheap fixes, in order)

Tone: opinionated, not balanced. If the direction is weak, say so. The lead
will re-weight your findings; they want raw signal, not consensus.

Hard rules:
  - Do NOT recommend the direction. Recommend *against* it where the evidence
    supports that. The lead's job is to balance.
  - Do NOT call any other subagent.
  - When done, return the document. STOP.
```

## Stage 2C: Adjacent opportunities

```
You are the OPPORTUNITY subagent. The lead picked one direction; your job is
to notice which OTHER directions from the brief become *newly feasible* as a
side effect of pursuing it.

Inputs:
  - Brief file:  ./brief.md
  - Chosen direction:  <the one the user picked>
  - The 2–4 other directions: <from brief.md>

Output: a single Markdown document with:
  ## Side Door #1: <title>
         (1 sentence: what becomes newly feasible, and why)
  ## Side Door #2: <title>
  ## Side Door #3: <title>
  ## What to Look Out For Mid-Implementation
         (specific signals during the main work that suggest opening a
         side door, e.g. "if loss plateaus before epoch 5, the encoder
         design is reusable for direction 3")
  ## What to NOT Pursue
         (1–2 directions from the brief that are dead ends, with reason)

Hard rules:
  - Don't propose new directions not in the brief.
  - Be specific: "side door #1 = direction 4" is more useful than "consider
    other directions".
  - When done, return the document. STOP.
```

---

## Stage 3: External validation

```
You are the EXTERNAL VALIDATION subagent. Your job: check if someone has
already done the chosen direction.

Inputs:
  - Direction title + 1-sentence pitch
  - Source paper, target paper
  - Keywords: <3–5 terms that should appear in any prior work>

Tools:  `whiskershelf-web-search` (use arxiv_search.py / s2_search.py /
        fetch_paper.py from the skill; do not browse the web blindly).

Output: a single Markdown document with:
  ## Prior Art
         (3–5 most-cited recent papers in this intersection, with
         title / year / venue / arxiv-id / 1-sentence takeaway)
  ## Closest Existing Work
         (the ONE paper that's most similar to the proposed direction,
         with a 1-paragraph comparison: what they did, what we'd do
         differently, what we can borrow)
  ## "The Land Is Empty" Verdict
         (one of: GREEN (no similar work, do it), YELLOW (some similar
         work, need to differentiate), RED (already done, don't do it))
  ## Citations to Add to the Brief
         (the 3–5 papers above, formatted as a "Related External Work" block
         ready to paste into brief.md or the working notes)

Hard rules:
  - Do NOT call other subagents.
  - If the search returns > 50 papers for a query, narrow it and re-search.
  - When done, return the document. STOP.
```

---

## Subagent output schemas (for the lead to parse)

All subagent outputs are Markdown documents. The lead can either:
- Concatenate them into one plan (simple, recommended for small projects).
- Parse out sections (if the lead wants to use specific subsections in
  different phases). The section headers (`## Core Idea`, `## First
  Concrete Experiment`, etc.) are stable and grep-friendly.

If a subagent's output is missing a required section, the lead should re-dispatch
with a tight scope: "you omitted `## Failure Modes`. Return just that section."
