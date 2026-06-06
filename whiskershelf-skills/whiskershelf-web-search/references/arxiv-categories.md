# arxiv Categories — A Quick Map for ML/AI Researchers

When you search arxiv, the **category filters** (`cat:` in the API) make the difference between 1000 results and 50. This is the subset that matters for the typical WhiskerShelf user (broad ML/AI with some systems / signals / vision).

## The "always relevant" core

| Code | Name | Notes |
|---|---|---|
| `cs.AI` | Artificial Intelligence | General AI; often co-listed with `cs.LG` |
| `cs.LG` | Machine Learning | The biggest single category; covers most ML preprints |
| `cs.CL` | Computation and Language | NLP, LLMs, language modeling |
| `cs.CV` | Computer Vision and Pattern Recognition | Vision, image, video |
| `cs.NE` | Neural and Evolutionary Computing | SNNs, neuro-inspired, evolutionary methods |
| `stat.ML` | Machine Learning (stat) | Mirror of `cs.LG` on the stat side; often has theory papers |

## Adjacent — frequently useful

| Code | Name | Notes |
|---|---|---|
| `cs.RO` | Robotics | RL for control, manipulation, VLA models |
| `cs.IR` | Information Retrieval | RAG, dense retrieval, embeddings |
| `cs.HC` | Human-Computer Interaction | Often has LLM-agent + UX work |
| `cs.CR` | Cryptography and Security | Adversarial ML, privacy, alignment |
| `cs.SY` | Systems and Control | Control theory, often co-listed with robotics |
| `cs.DC` | Distributed Computing | Model serving, distributed training |
| `eess.AS` | Audio and Speech Processing | Speech separation, ASR, TTS |
| `eess.IV` | Image and Video Processing | Medical imaging, codec |
| `eess.SP` | Signal Processing | Wireless, radar, communications (matches user's library!) |
| `q-bio.NC` | Neurons and Cognition | Neuroscience-flavored ML; SNN relevance |
| `math.OC` | Optimization and Control | Theory of training/optimization |

## Filtering API cheatsheet

The arxiv API (`http://export.arxiv.org/api/query`) supports these URL params:

| Param | Example | Notes |
|---|---|---|
| `search_query` | `abs:"spiking neural network"` | Field-scoped: `abs:`, `ti:`, `au:`, `cat:` |
| `cat` | `cat:cs.LG` | Comma-separated, OR semantics; combine with `AND` outside |
| `start` | `0` | Offset for pagination |
| `max_results` | `10` | Cap; the API also has hard limits |
| `sortBy` | `submittedDate` or `relevance` | Pair with `sortOrder` |
| `sortOrder` | `descending` | |

Useful search operators:
- `au:"Yann LeCun"` — author
- `ti:RWKV` — title
- `abs:"long context"` — abstract
- `cat:cs.LG AND cat:cs.CL` — both categories (AND across different fields)
- `cat:cs.LG OR cat:cs.NE` — either

## "Recent but not too recent" filter

arxiv doesn't have a "last 12 months" filter directly. To get last N months:

```python
import datetime as dt
cutoff = (dt.datetime.utcnow() - dt.timedelta(days=365)).strftime("%Y%m%d")
# arxiv YYYYMMDDHHMM date queries:
#   submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM]
query = f'cat:cs.LG AND submittedDate:[{cutoff}0000 TO 209912312359]'
```

The `scripts/arxiv_search.py` CLI does this for you with `--since YYYY` (year-only shortcut).

## Practical filters that work well

1. **For "what's new in X this year"**: `cat:cs.LG AND abs:"<term>" AND submittedDate:[<year>01010000 TO <year>12312359]`
2. **For "the canonical paper on X"**: `abs:"<exact term>"` + sort by `relevance`; cite the first 1-3.
3. **For "who's working on X"**: `au:"<author surname>"` + sort by `submittedDate` descending.

## Where arxiv falls short

- **Citation counts** are not in arxiv. Use Semantic Scholar for that.
- **Code links** are not in arxiv. Use Papers With Code.
- **Reviews / meta-decisions** are not in arxiv. Use OpenReview.
- **Paywalled venue papers** (e.g., some IEEE Trans.) may have arxiv preprints with different titles; if you can't find by title, search by first author.
