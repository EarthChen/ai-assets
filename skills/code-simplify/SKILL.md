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

Dispatch is justified by the scan's context weight, not by default — a small diff is faster inline.

- **Run this skill inline** when the diff is trivial, findings need live discussion mid-pass, scope or semantics require user input, or no subagent mechanism exists.
- **Dispatch audit, then resume the same agent to apply** when a subagent mechanism exists and the scan is heavy enough to belong out of the main session: dispatch in audit mode (read-only, return only the ranked findings record from `rules.md`), present it, then resume the same agent with the approved findings as an upper bound — not a work order: it still proves each one per `rules.md` and rejects with reason when proof fails. **Consent is risk-gated on the audit's own classification**: if every finding is provably safe (no production consumer, dynamic reachability ruled out) → resume directly, no human pause; if any finding is ambiguous or touches a public API / persisted format / compatibility path → present it and take the user's selection before resuming. Reusing the scan context avoids re-exploring the repo; the consent gate stays in the main session.
- **Dispatch apply end-to-end** when the user pre-approved the scope, the harness cannot resume agents, or overfitting is the concern and a fresh context judges it better: one agent executes `rules.md` from scan through verify. Never hand an audit findings list to a fresh agent as a fix order — that skips independent proof.
- If you cannot state the scope explicitly in the dispatch prompt, resolve it inline first — an ambiguous subagent dispatch silently falls back to the default scope.

## Execute

The execution rules live in [`rules.md`](rules.md) in this skill's directory — Establish The Scope → Understand Before Touching → Scan → Apply → Verify → Report. Read it and execute it end-to-end. Include this skill directory's absolute path in every dispatch prompt so the agent reads `rules.md` from there. The rules file is the single source of truth for both paths — never execute from memory.
