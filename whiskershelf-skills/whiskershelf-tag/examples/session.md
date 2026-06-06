# Example: tag session for a completed research direction

Scenario: the user finished a 2-week project on "SNN + RWKV-7 hybrid". They want to tag the relevant papers. Here's the agent's end-to-end flow.

## Step 1: read what the user has

```bash
python .claude/skills/whiskershelf-tag/scripts/check_presets.py --list
```

Output: 26 preset tags. The agent now has the catalog in mind.

## Step 2: read the brief's papers and their current tags

The brief lists 3 source papers. For each, read its current tags:

```bash
python .claude/skills/whiskershelf-tag/scripts/ws_tags_get.py "Spikformer v2.pdf"
# → 脉冲神经网络 SNN, Transformer

python .claude/skills/whiskershelf-tag/scripts/ws_tags_get.py "SpikeGPT Generative Pre-trained Language Model.pdf"
# → 脉冲神经网络 SNN, 大语言模型 LLM

python .claude/skills/whiskershelf-tag/scripts/ws_tags_get.py "RWKV-7 Goose with Expressive Dynamic State Evolution.pdf"
# → (no tags)
```

## Step 3: build the proposed tag set per paper

For each paper, propose what tags to add:

- **Spikformer v2** — already has `脉冲神经网络 SNN`, `Transformer`. The new project makes `线性注意力` relevant (the brief talks about WKV算子). Propose: add `线性注意力`. Keep existing.
- **SpikeGPT** — already has `脉冲神经网络 SNN`, `大语言模型 LLM`. Same addition. Propose: add `线性注意力`. Keep existing.
- **RWKV-7** — untagged. From the abstract, it's an LLM with linear attention. Propose: `大语言模型 LLM`, `线性注意力`, `架构创新`.

## Step 4: verify against presets

```bash
python .claude/skills/whiskershelf-tag/scripts/check_presets.py "线性注意力"
# → in_preset

python .claude/skills/whiskershelf-tag/scripts/check_presets.py --propose "大语言模型 LLM,线性注意力,架构创新"
# → all in_preset
```

If any candidate is missing from presets, this script will print "NOT in preset — would create a new custom tag" and suggest close matches. The agent should ask the user before adding custom tags.

## Step 5: show the user and confirm

```
Paper: Spikformer v2.pdf
  current (2): 脉冲神经网络 SNN, Transformer
  new     (3): 脉冲神经网络 SNN, Transformer, 线性注意力
  + add: 线性注意力
  = keep: 脉冲神经网络 SNN, Transformer

Paper: SpikeGPT Generative Pre-trained Language Model.pdf
  current (2): 脉冲神经网络 SNN, 大语言模型 LLM
  new     (3): 脉冲神经网络 SNN, 大语言模型 LLM, 线性注意力
  + add: 线性注意力
  = keep: 脉冲神经网络 SNN, 大语言模型 LLM

Paper: RWKV-7 Goose with Expressive Dynamic State Evolution.pdf
  current (0): (none)
  new     (3): 大语言模型 LLM, 线性注意力, 架构创新
  + add: 大语言模型 LLM, 线性注意力, 架构创新
```

User: "Looks good. Apply."

## Step 6: execute with dry-run first, then write

```bash
# Per paper, dry-run to show the diff, then apply.
python .claude/skills/whiskershelf-tag/scripts/ws_tags_set.py "Spikformer v2.pdf" \
    --tags "脉冲神经网络 SNN,Transformer,线性注意力" --dry-run

# User confirms. Now write.
python .claude/skills/whiskershelf-tag/scripts/ws_tags_set.py "Spikformer v2.pdf" \
    --tags "脉冲神经网络 SNN,Transformer,线性注意力"
```

Repeat for the other two papers. (Could be combined into a single approval if the user is confident, but per-paper is safer.)

## Step 7: read back and confirm

```bash
python .claude/skills/whiskershelf-tag/scripts/ws_tags_get.py "Spikformer v2.pdf"
# → 脉冲神经网络 SNN, Transformer, 线性注意力
```

Done. The library is now searchable by `线性注意力` and will surface this project's source material in future `whiskershelf-search` calls.

## Anti-patterns in this scenario

- Adding `架构创新` to all three papers because "they're all architecture papers". `架构创新` is for **novel** architectures; Spikformer/SpikeGPT/RWKV-7 are well-established, not novel. The preset's name is `架构创新` (innovation), not `架构` (architecture).
- Tagging every paper in the library "just in case" the project expands. Wait until the user actually pursues the expansion.
- Skipping the dry-run. The dry-run costs nothing and shows the exact diff; it catches typos in the comma-separated list.
- Writing without showing the user the current → new diff. Even with `--require-confirm`, the diff is what makes the change auditable.
