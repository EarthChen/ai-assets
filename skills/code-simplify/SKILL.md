---
name: code-simplify
disable-model-invocation: true
description: Simplify code inside one git scope (uncommitted changes, recent commits, or a full PR/MR diff) while preserving exact behavior.
---

# Simplify Changed Code

Simplify the code inside one git scope without changing what it does. For repo-wide dead-code removal and cross-module structural refactoring, use `refactor-clean` instead.

## Choose The Mode

- "audit" / "review" / "report" → inspect only; return ranked findings. Do not edit.
- "apply" / "simplify" / "clean up" → implement the safest findings and verify them.

## Routing

- **Dispatch the `code-simplifier` agent** when a subagent mechanism exists, the mode is apply, and the scope fits in one sentence of the dispatch prompt. Include the absolute path of this skill's directory in the dispatch prompt — the agent executes by reading `rules.md` there. A fresh context without conversation history also judges overfitting better.
- **Run this skill inline** when findings need discussion before edits, when scope or semantics require user input mid-pass, when the diff is trivial, or when no subagent mechanism exists.
- If you cannot state the scope explicitly in the dispatch prompt, resolve it inline first — an ambiguous subagent dispatch silently falls back to the default scope.

## Execute

The execution rules live in [`rules.md`](rules.md) in this skill's directory — Establish The Scope → Understand Before Touching → Scan → Apply → Verify → Report. Read it and execute it end-to-end; when dispatching, the agent reads it from the path you passed. The rules file is the single source of truth for both paths — never execute from memory.
