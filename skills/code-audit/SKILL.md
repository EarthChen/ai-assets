---
name: code-audit
disable-model-invocation: true
description: Deep, systematic code audit along three axes — Standards compliance, Spec fidelity against a diff, and language traps + cross-language review lenses (silent failure, type design, security). Dispatches three parallel sub-agents directly; never nested. For a Standards + Spec review of a diff alone (no language traps, no review lenses), use the mattpocock `code-review` skill (`mattpocock-skills:code-review` on Claude) instead.
---

# Code Audit

Audit code with three independent sub-agents — Standards, Spec, and Lang+Lens — dispatched in parallel as direct children of this session, never nested inside an intermediary agent. A change can pass one axis and fail another, so findings report side by side, never merged or re-ranked.

## Choose The Mode

- "audit" / "deep review" → inspect only; return ranked findings per axis. Do not edit.
- "apply" / "fix" → audit first, then apply only the findings the user selects, one at a time, verifying each (`rules.md`: Apply).

## Routing

Dispatch is justified by the scan's context weight, not by default — a single file audit is faster inline.

- **Run this skill inline** when the scope is one file or a trivial diff, findings need live discussion mid-pass, or no subagent mechanism exists.
- **Dispatch audit, then resume to apply** when a subagent mechanism exists and the scan is heavy enough to belong out of the main session: dispatch all three sub-agents in parallel in audit mode (read-only, each returning only its ranked findings record from `rules.md`), present them with their severity, take the user's selection, then resume with the selected findings as an upper bound — not a work order: each finding still gets proved per `rules.md` and rejected with reason when proof fails. Nothing the user did not select is applied. Reusing the scan context avoids re-exploring the repo; the consent gate stays in the main session. When the harness cannot resume agents, apply in the main session per `rules.md`: Apply. Never hand an audit findings list to a fresh agent as a fix order — that skips independent proof.
- If you cannot state the scope explicitly in the dispatch prompt, resolve it inline first — an ambiguous subagent dispatch silently falls back to the default scope.

## Execute

The execution rules live in [`rules.md`](rules.md) in this skill's directory — Establish The Scope → Select Axes → Execute → Aggregate → Report → Apply (fix mode only). Read it and execute it end-to-end. Include this skill directory's absolute path in every dispatch prompt so the agent reads `rules.md` from there. The rules file is the single source of truth for both paths — never execute from memory.
