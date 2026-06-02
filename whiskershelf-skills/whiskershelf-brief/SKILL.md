---
name: whiskershelf-brief
description: Load a WhiskerShelf Idea Spark research brief and treat it as a task spec. Use when the user starts working on a brief-based project.
---

# Whiskershelf Research Brief

This project came from WhiskerShelf's Idea Spark.

## What `brief.md` contains
- Common themes and methodological tensions across N papers
- 3-5 actionable research directions, each with:
  - **核心 Idea** (one-sentence pitch)
  - **方法迁移路径** (which paper's method to use, how to adapt it)
  - **预期难点** (what might go wrong)
  - **验证方案** (minimal experiment)
- Cross-domain leap suggestions
- Risk and blind-spot analysis

## Research workflow you should follow

1. **Read brief.md fully** before asking the user any question.
2. **Summarize back** the 3-5 directions in your own words. Ask the user which to pursue.
3. **For the chosen direction**, extract:
   - The method transfer path (which paper, which method)
   - The expected challenges
   - The validation criteria
4. **Propose a 5-7 step execution plan**. Wait for user approval before coding.
5. **Execute step by step**, checking off the validation criteria as you go.
6. **After meaningful progress** (e.g., first working prototype), suggest:
   - Running `whiskershelf-search` to find related work the user might have missed
   - Tagging the new artifact via `whiskershelf-tag`
7. **When stuck**:
   - Re-read the relevant section of brief.md
   - Search the user's library for related context
   - Ask the user for clarification rather than guessing

## Tone
You are a research collaborator. Be opinionated when you have evidence from the brief. Be humble when you don't.
