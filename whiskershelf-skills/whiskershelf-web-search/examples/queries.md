# Example: web-search session for a brief direction

Scenario: the brief's first direction is "把 RWKV-7 的状态演化机制迁移到脉冲域". The user has Spikformer and SpikeGPT in the library, but the local search is silent on "RWKV". The agent now needs to (a) confirm the canonical RWKV-7 paper, (b) check if anyone has tried SNN+RWKV, and (c) find a recent SNN training survey for context.

## Step 1: canonical RWKV-7 paper

```bash
python .claude/skills/whiskershelf-web-search/scripts/arxiv_search.py \
    --query 'au:"Bo" AND abs:"RWKV"' --max 5
```

This typically surfaces the RWKV-7 paper directly. Pin the arxiv id (e.g. `2503.14456`).

## Step 2: has anyone done SNN+RWKV?

```bash
python .claude/skills/whiskershelf-web-search/scripts/arxiv_search.py \
    --query 'abs:"spiking" AND abs:"RWKV"' --max 10 --since 2024
```

If 0 results, the combination is novel — that's a strong signal for the brief's first direction. If 1-3, the user needs to differentiate explicitly. If 5+, this direction is too crowded; consider a more specific angle (e.g., combining with attention, or with a specific SNN encoding scheme).

## Step 3: SNN training survey for context

```bash
python .claude/skills/whiskershelf-web-search/scripts/s2_search.py \
    --query "spiking neural network training survey" \
    --max 3 --min-citations 50
```

Sort by citation count via `--min-citations` to find the most-established review. The first hit is usually the right starting point for a 2-page synthesis.

## Step 4: drill into one paper

```bash
python .claude/skills/whiskershelf-web-search/scripts/fetch_paper.py --arxiv 2503.14456
```

This gives you title, authors, year, abstract, categories, abs URL, and PDF URL. From here you can decide whether to read the PDF (with `WebFetch` on the abs URL) or just cite it.

## Step 5: synthesize and report back

The skill's `SKILL.md` specifies a "Related External Work" section format. Append to your working notes:

```
### Related external work (from whiskershelf-web-search)
- **RWKV-7: Goose with Expressive Dynamic State Evolution** (2025, arXiv): introduces data-dependent decay; the mechanism we want to port to SNN. https://arxiv.org/abs/2503.14456
- **Spikformer v2** (the local copy in your library): our target architecture.
- **Training Spiking Neural Networks Using Lessons from Deep Learning** (2023, arXiv): a useful survey for surrogate-gradient design. https://arxiv.org/abs/2308.01219
- (no prior work found combining RWKV with SNN — possible research opportunity)
```

## Step 6: surface the competitive-landscape finding to the user

> "I checked arxiv for prior work on SNN+RWKV. There are 0 papers at the exact intersection as of 2026-06. The closest are X and Y, which do [X] and [Y] but not the combination. This direction is open. Two things to verify before committing: (1) the RWKV-7 decay is mathematically well-defined for binary spike inputs — I think yes but want to confirm; (2) the surrogate gradient design is the main risk. Want me to plan the minimum reproduction?"

This is what "research collaborator" means: don't just dump a list, give a recommendation with the reasoning.

## Anti-patterns in this scenario

- Going to Google Scholar before arxiv. arxiv has the data in structured form, Scholar is a web scrape.
- Re-using the same query across all 4 steps. Each step has a specific question (canonical / overlap / context / detail); each needs its own query.
- Stopping at "no prior work found" without checking that the search was correct (e.g., trying "linear RNN" and "linear attention" as synonyms).
- Quoting the full abstract into the response — `fetch_paper.py` already gives you the first 200 chars in human mode; the user can read the rest from the URL.
