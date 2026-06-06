# Research Workflow Patterns

A reference for the kinds of research workflows the user is likely to launch via WhiskerShelf. Use this to anticipate what they want and to know when to switch modes.

## Pattern A — "Re-implement and verify" (most common)

The user picks 2–4 papers, the brief suggests combining their methods, the user wants code that demonstrates the method on a small dataset.

**Stages**:
1. Read paper X's method section closely (`whiskershelf-search` for the abstract; `whiskershelf-web-search` for the official PDF if missing locally).
2. Build a minimum-viable reproduction. Single-file, single-GPU, ≤ 4 hours of compute.
3. Verify on a toy dataset. Plot loss curves. Check that loss goes down and a baseline metric improves.
4. Iterate: ablation, hyperparameter sweep, sanity checks.
5. Write up: results table, 1-paragraph discussion, 1 figure.

**Skill chain**: `whiskershelf-brief` → `whiskershelf-subagents` (Stage 1 + 2 in parallel) → `whiskershelf-search` (find related work) → `whiskershelf-web-search` (check SOTA) → `whiskershelf-tag` (organize outputs).

## Pattern B — "Comparative analysis" (no code)

The user wants a written synthesis: which paper is best for what, where do they disagree, what's the right one to read first.

**Stages**:
1. Read all selected papers' abstracts + your notes.
2. For each, identify: core claim, methodology, key result, known limitation.
3. Build a comparison table (rows = papers, columns = dimensions).
4. Write a 2-page synthesis with a recommendation.

**Skill chain**: `whiskershelf-brief` → `whiskershelf-search` (fetch abstracts) → write. No subagents needed unless the user asks for a "deep comparison".

## Pattern C — "Propose a new direction" (exploratory)

The brief itself is the deliverable; the user wants to expand it, find more candidate directions, or stress-test one.

**Stages**:
1. Re-read the brief's 3–5 directions.
2. For the chosen direction, dispatch 2–3 subagents in parallel (method transfer, risk analysis, adjacent opportunities) per `whiskershelf-subagents` Stage 2.
3. Optionally do external validation (`whiskershelf-subagents` Stage 3).
4. Synthesize a refined direction with updated method path + challenges.
5. Present to the user; iterate.

**Skill chain**: `whiskershelf-brief` → `whiskershelf-subagents` (heavy use) → `whiskershelf-web-search` (Stage 3) → `whiskershelf-tag` (record the new direction as a tag).

## Pattern D — "Reproducibility audit"

The user has a paper, suspects a result is wrong, and wants a careful re-examination.

**Stages**:
1. Re-read the paper's experiment section.
2. Identify each reported number, the dataset it was on, and the protocol.
3. Look for: data leakage, undisclosed preprocessing, hyperparameter sensitivity, missing ablations.
4. Propose specific re-runs to test each claim.

**Skill chain**: `whiskershelf-search` (get abstract + notes) → `whiskershelf-web-search` (find follow-up papers that already did this) → write audit.

## When to switch patterns

If the user says "actually, let's just write it up" mid-implementation, switch from A to B. If they say "wait, is this even a good idea?" mid-coding, switch to C and dispatch a subagent to stress-test the direction. Don't keep grinding on a plan the user has lost faith in.
