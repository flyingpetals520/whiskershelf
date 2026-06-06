# Tag Taxonomy — The Preset List

WhiskerShelf ships with 27 preset tags (defined in `tag_presets.json`). The user can add custom tags via the UI; the agent should **prefer presets** to avoid drift.

The full list (verified 2026-06-06):

| Tag | When to apply | Closest non-preset alternatives to NOT use |
|---|---|---|
| `Agent` | LLM agents, tool use, multi-step reasoning, agentic frameworks | "Agentic" / "Multi-agent" — keep on preset only |
| `AI Infra` | Training infra, model serving, distributed training, compilers | "Systems", "MLOps" — usually synonyms, prefer preset |
| `Transformer` | Anything built on transformer architecture (encoder/decoder, attention) | "Attention", "Self-attention" — fine as descriptive but tag the paper as `Transformer` |
| `世界模型` | World models, JEPA-style predictive architectures, model-based RL | "World modeling" — keep CJK |
| `优化器` | Optimizer design (Muon, Adam variants, LR schedules) | "Optimization" — too broad; be specific |
| `图像生成` | Image generation, diffusion for images, image editing | "Image synthesis", "Image editing" — covered by preset |
| `垂直领域应用` | Domain applications (medical, legal, finance, scientific) | "Application" — keep preset |
| `多模态` | Multimodal models (vision-language, audio-language, etc.) | "Vision-language", "VLM" — preset is broader |
| `大语言模型 LLM` | LLMs, foundation models, pretraining for language | "Foundation model" — only when language-specific |
| `开源模型` | Open-source model releases (weights + code public) | "Open-source", "OSS" — keep preset wording |
| `强化学习 RL` | RL algorithms, RLHF, GRPO, PPO, DPO, etc. | "RLHF", "Alignment" — DPO is RL, tag both |
| `扩散模型` | Diffusion language models, score-based generation | "Flow matching" — flow matching is its own family; consider both `扩散模型` + a custom tag |
| `技术报告` | Vendor tech reports (GPT-4, GLM-5, etc.) | "Report" — too vague |
| `机器人` | Robotics, manipulation, navigation, VLA models | "Embodied AI", "Robotic learning" — covered |
| `架构创新` | Novel architectures / mechanisms, not just scaling | "Novel architecture", "New method" — covered |
| `理论分析` | Theory, convergence, scaling laws, expressiveness | "Theory" — covered |
| `神经形态计算` | Neuromorphic hardware, event-driven, BrainScaleS, Loihi | "Neuromorphic" — covered |
| `线性注意力` | Linear attention, state-space, RWKV, Mamba, DeltaNet | "Linear-time attention" — covered |
| `脉冲神经网络 SNN` | SNN training, spiking backprop, neuromorphic algorithms | "Spiking NN" — keep preset wording |
| `脑科学` | Neuroscience, brain mapping, cortical models | "Computational neuroscience" — covered |
| `视频生成` | Video generation, video editing, video prediction | "Video synthesis" — covered |
| `计算机视觉 CV` | Classical CV, recognition, detection, segmentation | "Vision" — too broad |
| `训练方法` | Training recipes, data augmentation, regularization | "Training" — too vague; preset is specific |
| `记忆网络` | Memory networks, KV compression, retrieval-augmented models | "Memory" — keep preset |
| `语音音频` | Speech, audio, music, TTS, ASR, separation | "Speech" — covered |
| `长上下文` | Long-context modeling, RAG, KV cache, context extension | "Long context" — keep CJK / spacing |
| `高效推理` | Inference optimization, quantization, pruning, distillation | "Inference", "Efficient inference" — covered |

## Disambiguation rules

Papers often sit at the intersection of two or more tags. Apply all that genuinely apply — don't be stingy, but don't pad either. Common cross-tags in this library:

- **`大语言模型 LLM` + `Transformer`**: most LLM papers. Both.
- **`大语言模型 LLM` + `强化学习 RL`**: any RLHF/DPO/GRPO paper. Both.
- **`大语言模型 LLM` + `长上下文`**: any long-context LLM. Both.
- **`线性注意力` + `架构创新`**: linear attention is itself architectural innovation. Both.
- **`脉冲神经网络 SNN` + `神经形态计算`**: spiking + hardware → both. Pure-algorithm SNN → just SNN.
- **`多模态` + `计算机视觉 CV`**: VLM papers often deserve both.
- **`扩散模型` + `图像生成` / `视频生成`**: image/video diffusion → both. Diffusion LMs (without image/video) → just `扩散模型`.
- **`架构创新` + `训练方法`**: rare; usually one or the other. If the paper introduces a method and a recipe, both.
- **`Agent` + `强化学习 RL`**: agentic RL (e.g. RL on tool use). Both.
- **`理论分析` + anything**: theory work almost always has a `理论分析` tag. Apply it last, after picking the topical tags.

## What NOT to tag

- **Quality / status**: "important", "to-read", "skimmed" — these go in `paper_reading.json` (stars, read counts) or in the user's notes, not in tags.
- **Source / venue**: "NeurIPS", "arxiv" — the user already filters by year/folder. Adding a venue tag creates noise.
- **Year**: "2024", "2025" — same. The user has timestamps.
- **One-off descriptive terms**: "weird", "controversial", "must-cite" — these belong in `notes`, not in the global tag list.

## Adding a new custom tag

If the user wants a tag that isn't in the preset list:

1. Use `check_presets.py --propose <tag>` to verify it's not already a preset under a different name.
2. Scan the library for similar custom tags the user has already created (e.g., `ws_papers.py` + filter by tag).
3. Propose the new tag in the same way you propose a tag change, with the rationale.
4. If the user approves, add it via the normal write flow.

**Don't** invent a new tag without asking. Taxonomy drift is the silent killer of personal libraries.
