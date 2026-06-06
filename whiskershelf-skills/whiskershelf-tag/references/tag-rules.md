# Tag Rules — How to Apply Tags Well

Practical rules the SKILL.md can't say without bloating. Read this once; refer back when you're not sure.

## The "5-tag ceiling" rule

A paper with 5+ tags is usually a sign of over-tagging. The user can filter the library; over-tagged papers match every filter and become useless. **Aim for 2–4 tags per paper.** 5 is the soft cap; if you're tempted to add a 6th, drop the weakest first.

What "weakest" means:
- A tag that's implied by another (e.g., `Transformer` + `架构创新` is fine, but `Transformer` + `Attention` is redundant).
- A status tag ("to-read") — those don't go in the tag list.
- A "vibe" tag ("interesting", "weird") — those go in notes.

## The "did the user say so?" rule

Don't tag for the user. The user is the only one who knows what they want to find later. Your job is to:
- Propose based on the abstract and the existing tag scheme.
- Surface your reasoning so the user can correct.
- Apply after the user confirms.

This is the gating workflow in the SKILL.md. Re-read it whenever you're tempted to "just write it, the change is obvious".

## Read existing tags first

```bash
python .claude/skills/whiskershelf-tag/scripts/ws_tags_get.py "Spikformer v2.pdf"
```

Existing tags are the user's prior mental model. Don't churn them just because you have a new idea — extend, don't replace.

When merging similar papers' tags (e.g., "Spikformer v2" and "Spiking_ResFormer"), look at both tag lists first. If the user has consistently used `脉冲神经网络 SNN` for both, the new paper should get that tag too.

## Tagging new artifacts vs. papers

This skill is for tagging **papers in the library**. The user also creates:
- Project subfolders (output of Idea Spark → CC project)
- Code files inside a project
- Notes files
- Plot images

These are **not** managed by the WhiskerShelf tag API. If the user wants to "tag" a code file, suggest putting it in a subfolder named after a tag, or use a comment header. Don't try to push code-file tags through the API.

## The "tag vs. note" decision

| Want to record… | Use |
|---|---|
| Topic / category | Tag |
| "Important" / "skim" | Star + read count (UI) |
| "I disagreed with this paper" | Notes |
| "Cited by 50 follow-ups" | Notes (or `whiskershelf-web-search`) |
| "Re-read before writing the related work" | Notes |
| "Belongs to project X" | Tag (or subfolder for the project) |

Notes are free-form. Tags are for filtering. Pick the right tool.

## "Adjacent opportunity" tagging

When `whiskershelf-brief` produces a 3-direction brief and the user picks direction 1, the OTHER directions often become "now interesting" because the implementation surfaced adjacent methods. Don't tag those other directions' papers automatically — the user might never pursue them. Mention them in the conversation; let the user tag.

## When the user says "tag everything about X"

This is the only time a batch operation is appropriate. The flow:

1. `ws_papers.py --tag "X" --name-only` → see what's already tagged.
2. `ws_papers.py --json` → full library, filter in your head for "about X".
3. Propose the list (paper-by-paper), get user approval, then loop the write.
4. The 3-step gating still applies per paper; the "yes" can be a single approval for the whole batch if the user wants speed.

## When the user says "untag Y" or "remove the X tag from these papers"

Same workflow, but the diff is "remove". Show the user the list of papers currently tagged X, ask which to remove from, then `POST` with the new (shorter) tag list for each.

If a paper currently has `[X, A, B]` and the user wants to drop `X`, you POST `[A, B]` — not `[A, B, X]` or `[]`. Always read-then-write.
