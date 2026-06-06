# Query Templates

Starter queries for common research scenarios. Customize the bracketed placeholders. The shape works for both `WebSearch` and the `scripts/arxiv_search.py` / `scripts/s2_search.py` CLIs.

## "What's new in X?"

```
"<X>" [cat:cs.LG | cat:cs.CL | ...] [submittedDate:[YYYY01010000 TO YYYYMMDDHHMM]]
```

Examples:
- `"world model" cat:cs.LG submittedDate:[202501010000 TO 202606312359]`
- `"long context" cat:cs.CL submittedDate:[202501010000 TO 202606312359]`

## "Has anyone done X for Y?"

```
"<method>" AND "<application>" [cat:cs.<X> AND cat:cs.<Y>]
```

Examples:
- `"spiking neural network" AND "time series" cat:cs.NE`
- `"RWKV" AND "multimodal" cat:cs.CL AND cat:cs.CV`

If this returns 0, that's a real signal — possible research opportunity. If 50, the area is saturated — narrow.

## "Citing/finding follow-ups to a known paper"

Semantic Scholar: `/paper/<id>/citations?fields=title,year,venue,url&limit=20`

```
S2: <paper title or arxiv id> -> "cited by" -> 20 most recent
```

Examples:
- arXiv:1706.03762 (Transformer) — too many, narrow to year 2024+
- arXiv:2303.08774 (GPT-4 tech report) — narrow to 2025+

## "Find the canonical paper"

```
abs:"<exact technical term>"  sortBy=relevance
```

Examples:
- `abs:"test-time training"` (find the first / most-cited TTT paper)
- `abs:"state space model"` (find S4, S5, Mamba lineage)
- `abs:"linear attention"` (find Performer, Linformer, etc.)

## "Author's recent work"

```
au:"<surname>" sortBy=submittedDate
```

Examples:
- `au:"LeCun" cat:cs.LG` — Yann's recent
- `au:"Touvron"` — Hugo Touvron (LLaMA, etc.)
- `au:"Gu"` — Albert Gu (Mamba)

## "SOTA on benchmark X"

Use Papers With Code:
- Browse: `https://paperswithcode.com/sota/<task-slug>`
- API: `GET /api/v1/tasks/?q=<task>`

Examples:
- `sota/image-classification-on-imagenet`
- `sota/question-answering-on-gpqa`

## "Code available?"

```
"<paper title>" site:github.com
```

If the search returns a GitHub repo with stars, you've found the canonical implementation. If only a third-party reimplementation, note the gap.

## Field-specific template banks

### Spiking Neural Networks (SNN)
- `"surrogate gradient" snn cat:cs.NE`
- `"spike-driven" "spike-driven transformer"`
- `"LIF" "leaky integrate-and-fire" "backpropagation"`
- `"neuromorphic" cat:cs.NE`
- `au:"Roy" "K" "snn"` (Kaushik Roy is prolific)

### Linear attention / state-space models
- `"linear attention" "state space"`
- `"Mamba" cat:cs.LG`
- `"RWKV" "linear recurrence"`
- `"DeltaNet" "Gated DeltaNet"`

### Long context
- `"long context" "RoPE" "YaRN"`
- `"needle in haystack" benchmark`
- `"context window" extension`

### RL / RLHF
- `"RLHF" "DPO" cat:cs.LG`
- `"GRPO" "reasoning"`
- `"process reward model" cat:cs.LG`

### Diffusion / generative
- `"flow matching" cat:cs.LG`
- `"consistency model" diffusion`
- `"diffusion language model"`

## What doesn't work

- **Long boolean expressions with 5+ ANDs** — returns near-zero. Loosen to 2-3 terms + a year filter.
- **Quotes around phrases longer than 5 words** — most abstracts don't use that exact phrase. Use individual key terms.
- **Author search with full name** — `au:"LeCun, Yann"` is brittle. Use just the surname for broad, or full name with quotes for disambiguation.

## If your query returns nothing

1. Drop the year filter (maybe the work is older than you think).
2. Try the parent field (e.g., `cs.LG` instead of `cs.NE`).
3. Try a synonym (e.g., "spike" instead of "action potential", or "policy gradient" instead of "REINFORCE").
4. Search by the method's first author.
5. **Accept that the work may not exist** — that's a research finding, not a search failure.
