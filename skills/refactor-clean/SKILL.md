---
name: refactor-clean
disable-model-invocation: true
description: Repo-wide entropy reclamation — prove and safely remove dead code, duplicate representations, speculative generality, and over-engineering.
---

# Reclaim Code Entropy

Treat code entropy as maintenance surface with no current load-bearing reason: extra representations, states, APIs, branches, packages, policies, or tests that the product must keep coherent.

This skill is repo-wide by design — cross-module dead code, duplicated truths, and structural over-engineering. For simplifying one git scope (uncommitted changes, recent commits, a PR/MR diff), use `code-simplify` instead.

## Choose The Mode

- For "audit", "find", "review", or "report", inspect only and return ranked candidates. Do not edit.
- For "apply", "remove", "clean up", "simplify", or "refactor", implement the safest requested cuts and verify them.
- Treat removal of a reachable user capability, supported public API, persisted format, or compatibility path as a product decision. Surface the visible tradeoff before changing it unless the user already made that decision explicitly.

## Routing

Dispatch is justified by the survey's context weight, not by default — a narrow target area is faster inline.

- **Run this skill inline** when the target area is narrow, findings need discussion before any deletion, a cut is a product decision the user has not made, or no subagent mechanism exists.
- **Dispatch audit, then resume the same agent to apply** when a subagent mechanism exists and the survey is heavy enough to belong out of the main session: dispatch in audit mode (read-only, return only the ranked candidates record from `rules.md`), present it, then resume the same agent with the approved candidates as an upper bound — not a work order: it still proves each one per `rules.md` and rejects with reason when proof fails. **Consent is risk-gated on the audit's own SAFE/CAREFUL/RISKY classification**: all SAFE → resume directly, no human pause; any CAREFUL (dynamic imports / string-based references) or RISKY (public API surface, persisted format, compatibility path) → present it and take the user's selection before resuming. Reusing the survey context avoids re-exploring the repo; the consent gate stays in the main session.
- **Dispatch apply end-to-end** when the user pre-approved the target area or the harness cannot resume agents: one agent executes `rules.md` from survey through validate. Heavy, context-dense work belongs out of the main session. Never hand an audit candidates list to a fresh agent as a fix order — that skips independent proof.
- If you cannot state the target area explicitly in the dispatch prompt, scope it inline first — an ambiguous subagent dispatch widens the blast radius.

## Execute

The execution rules live in [`rules.md`](rules.md) in this skill's directory — Establish The Contract → Survey For Entropy → Prove Or Reject → Implement → Validate → Report. Read it and execute it end-to-end. Include this skill directory's absolute path in every dispatch prompt so the agent reads `rules.md` from there. The rules file is the single source of truth for both paths — never execute from memory.
