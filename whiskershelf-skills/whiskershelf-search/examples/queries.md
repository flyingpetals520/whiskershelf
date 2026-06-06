# Example: Multi-step search session

The user's brief says "investigate SNN training stability on long sequences". Here's how an agent should approach it, end-to-end.

## Step 1: broad sweep

```bash
python .claude/skills/whiskershelf-search/scripts/ws_search.py "spiking neural network"
```

If this returns 5+ papers, the user has a solid base. If 0–1, the topic is under-represented locally and you should suggest `whiskershelf-web-search`.

## Step 2: narrow by technique

```bash
python .claude/skills/whiskershelf-search/scripts/ws_search.py "surrogate gradient"
python .claude/skills/whiskershelf-search/scripts/ws_search.py "STDP"
```

These are **literal substrings** the search will find if the abstract uses them. If you get nothing, try synonyms: `"spike-timing"`, `"LIF"`, `"leaky integrate-and-fire"`, `"膜电位"`.

## Step 3: drill into a specific paper

Once you have a candidate from Step 1, fetch the full record:

```bash
python .claude/skills/whiskershelf-search/scripts/ws_detail.py "Spikformer v2.pdf" --notes-only
```

`--notes-only` is the right flag here — the user said "investigate" which means they want to recall what they already noted. The abstract is for the paper; the notes are for the user's past thinking.

## Step 4: cross-check with tags

```bash
python .claude/skills/whiskershelf-search/scripts/ws_papers.py --tag "脉冲神经网络 SNN" --name-only
```

Use `--name-only` to feed the file list into the next step (e.g. summarize by tag, or hand to a subagent per `whiskershelf-subagents`).

## Step 5: surface the answer to the user

After all four steps, you should be able to answer:
- "You have N papers on SNN training; K of them touch long sequences specifically."
- "Of those, paper X has the most detailed notes — that's your starting point."
- "Paper Y exists but is tagged `脑科学`, not SNN — relevant?"

Don't proceed to implementation until the user has picked a starting paper.

## Common anti-patterns

- Searching 10 synonyms when the first one returned 30 results — you have enough.
- Skipping `ws_detail.py` and going straight to implementation from a 300-char preview.
- Forgetting to check `notes`. Notes are the highest-signal field; many users write more in notes than the abstract justifies.
