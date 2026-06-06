# Example: 4-subagent dispatch session

Scenario: the user picked direction 1 from the SNN+RWKV brief, and asks "give me a complete plan before I commit a week to this". The lead's job: dispatch, then synthesize.

## Step 0: load the brief and parse

```bash
python .claude/skills/whiskershelf-brief/scripts/parse_brief.py brief.md --direction 0
```

(returns: direction 1 = "把 RWKV-7 的状态演化机制迁移到脉冲域")

## Step 1: build a dispatch plan

```bash
python .claude/skills/whiskershelf-subagents/scripts/dispatch_pipeline.py brief.md --direction 0
```

Output (in human mode):
```
# Dispatch Plan for Direction 0: 把 RWKV-7 的状态演化机制迁移到脉冲域

Brief: ./brief.md
Papers (3):
  - SpikeGPT Generative Pre-trained Language Model.pdf
  - SPIKFORMER v2.pdf
  - RWKV-7 Goose with Expressive Dynamic State Evolution.pdf

Total subagents to dispatch in one parallel batch: 6

[1] Stage 1 — per-paper
    purpose: Deep dive on SpikeGPT Generative Pre-trained Language Model.pdf
    paper:   SpikeGPT Generative Pre-trained Language Model.pdf
[2] Stage 1 — per-paper
    purpose: Deep dive on SPIKFORMER v2.pdf
    paper:   SPIKFORMER v2.pdf
[3] Stage 1 — per-paper
    purpose: Deep dive on RWKV-7 Goose with Expressive Dynamic State Evolution.pdf
    paper:   RWKV-7 Goose with Expressive Dynamic State Evolution.pdf
[4] Stage 2A — method-transfer
    purpose: Design transfer pipeline for direction 1: ...
[5] Stage 2B — risk
    purpose: Attack the direction; surface failure modes
[6] Stage 2C — adjacent
    purpose: Find side doors / adjacent opportunities
[7] Stage 3 — external-validation
    purpose: Check arxiv + S2 for prior art; return GREEN/YELLOW/RED verdict
```

The `--max-papers` flag caps the per-paper subagents; for a 5-paper project, set `--max-papers 3` and merge the other 2 into "background context" instead.

## Step 2: dispatch all 7 in parallel

The lead fires 7 `Task` tool calls **in a single message**. Each prompt is from `references/subagent-templates.md` with the appropriate substitutions. Example for the Stage 1 subagent on RWKV-7:

```
You are analyzing one paper from a WhiskerShelf Idea Spark brief.

Inputs:
  - Brief file:  ./brief.md
  - Paper name:  RWKV-7 Goose with Expressive Dynamic State Evolution.pdf
  - Your scope:  ONLY this paper. Do not analyze the others.

Steps:
  1. Fetch the paper's full abstract:
       GET http://127.0.0.1:8080/api/agent/papers/RWKV-7%20Goose%20with%20Expressive%20Dynamic%20State%20Evolution.pdf
     (Whiskershelf must be running. If the call fails, say so and stop.)
  ...
```

Stage 2A prompt needs source/target filled in. The lead picks `RWKV-7` (source) and `Spikformer v2` (target) because that's what the brief's "方法迁移路径" suggests.

## Step 3: wait for all 7 reports

Subagents return in 1–3 minutes typically. Don't poll — the runtime notifies the lead when they're all done.

## Step 4: synthesize

The lead (not a subagent) writes the execution plan using the template in `references/dispatch-patterns.md`. Pull from each subagent's report:

- Phase 0/1 setup → from the relevant Stage 1A's "Re-implementation Skeleton"
- Phase 2 transfer → from Stage 2A's "First Concrete Experiment"
- Phase 3 risks → from Stage 2B's "Most Likely Negative Result"
- Phase 4 writeup → standard
- "What could derail" → from Stage 2B
- "Side doors" → from Stage 2C
- "External landscape" → from Stage 3's verdict

A 2-page plan, ~10 minutes of lead work.

## Step 5: present to the user, then STOP

```
# Execution Plan: 把 RWKV-7 的状态演化机制迁移到脉冲域

> Confidence: MEDIUM (low prior art, but a real risk on surrogate gradient design)

## TL;DR
We replace Spikformer's LIF decay with RWKV-7's data-dependent state decay,
keep the spike encoding + SSA backbone, and target N-Caltech-101. The win
is sparsity + better long-range memory; the main risk is surrogate gradient
stability on the new decay term. Prior-art check found 0 direct combinations
(GREEN) but several adjacent ones (cite below).

## Phase 0: Setup
- [ ] Install snnTorch + torch 2.x
- [ ] Download N-Caltech-101 (or use a DVS128 Gesture subset for fast iteration)
- [ ] Clone the Spikformer v2 reference repo

## Phase 1: MVP (Day 1-3)
[... 4-5 bullets from Stage 1A's skeleton ...]

## Phase 2: Transfer (Day 3-7)
[... from Stage 2A's first experiment ...]

## What could derail this
- Surrogate gradient may not converge with data-dependent decay (Stage 2B's #1)
- RWKV-7's decay has a `time_decay` initial value that's hard to set correctly (Stage 2B's #2)

## Side doors
- If decay works, the same mechanism could be ported to audio (Direction 2 from brief)
- If it doesn't, the data-dependent gate itself is publishable as a NeurIPS workshop paper

## External landscape
GREEN: 0 prior papers on SNN+RWKV at the exact intersection.
Cite: Peng et al. 2025 (RWKV-7, arXiv:2503.14456); Zhou et al. 2023 (Spikformer v2); Fang et al. 2024 (Training SNN survey).
```

User reviews, says "Phase 1 only, I'll decide on Phase 2 after seeing the loss curves". Lead adjusts, then starts Phase 1.

## Common failure modes in this scenario

- Dispatching only 2 of the 7 subagents ("the brief is clear enough"). The skill exists because the brief usually isn't; the missing subagents would have caught things the lead didn't.
- The Stage 2B risk subagent returns "this will fail" and the lead ignores it because the user is excited. The lead's job is to surface the risk to the user, not to make the user happy.
- The Stage 3 external-validation subagent returns RED (already done). The lead should immediately halt and tell the user, not try to differentiate.
- Synthesizing the plan *before* all 7 subagents return. Wait for all of them. Partial synthesis misses the inputs from the late ones.
- Coding Phase 1 before the user explicitly approves. "Phase 1 only" is still an approval; "looks good" without phase-scoping is not.
