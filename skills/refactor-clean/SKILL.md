---
name: refactor-clean
disable-model-invocation: true
description: Repo-wide entropy reclamation — prove and safely remove dead code, duplicate representations, speculative generality, and over-engineering; executed inline or via the refactor-cleaner agent.
---

# Reclaim Code Entropy

Treat code entropy as maintenance surface with no current load-bearing reason: extra representations, states, APIs, branches, packages, policies, or tests that the product must keep coherent.

This skill is repo-wide by design — cross-module dead code, duplicated truths, and structural over-engineering. For simplifying one git scope (uncommitted changes, recent commits, a PR/MR diff), use `code-simplify` instead.

## Choose The Mode

- For "audit", "find", "review", or "report", inspect only and return ranked candidates. Do not edit.
- For "apply", "remove", "clean up", "simplify", or "refactor", implement the safest requested cuts and verify them.
- Treat removal of a reachable user capability, supported public API, persisted format, or compatibility path as a product decision. Surface the visible tradeoff before changing it unless the user already made that decision explicitly.

## Routing

- **Dispatch the `refactor-cleaner` agent** when a subagent mechanism exists, the mode is apply, and the target area fits in one sentence of the dispatch prompt. Include the absolute path of this skill's directory in the dispatch prompt — the agent executes by reading `rules.md` there. Heavy, context-dense work belongs out of the main session.
- **Run this skill inline** when findings need discussion before any deletion, when a cut is actually a product decision the user has not made, or when no subagent mechanism exists.
- If you cannot state the target area explicitly in the dispatch prompt, scope it inline first — an ambiguous subagent dispatch widens the blast radius.

## Execute

The execution rules live in [`rules.md`](rules.md) in this skill's directory — Establish The Contract → Survey For Entropy → Prove Or Reject → Implement → Validate → Report. Read it and execute it end-to-end; when dispatching, the agent reads it from the path you passed. The rules file is the single source of truth for both paths — never execute from memory.
