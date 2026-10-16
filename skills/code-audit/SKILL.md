---
name: code-audit
disable-model-invocation: true
description: Deep code audit along three axes: Standards compliance, Spec fidelity against a diff, and language traps plus cross-language lenses (silent failure, type design, security). For a Standards + Spec review alone, use the mattpocock `code-review` skill.
---

# Code Audit

Audit code with three independent sub-agents — Standards, Spec, and Lang+Lens — dispatched in parallel as direct children of this session, never nested inside an intermediary agent. A change can pass one axis and fail another, so findings report side by side, never merged or re-ranked.

## Choose The Mode

- "audit" / "deep review" → inspect only; return ranked findings per axis. Do not edit.
- "apply" / "fix" → audit first, then apply only the findings the user selects, one at a time, verifying each (`rules.md`: Apply).

## Routing

Dispatch is justified by the scan's context weight, not by default — a single file audit is faster inline.

- **Run this skill inline** when the scope is one file or a trivial diff, findings need live discussion mid-pass, or no subagent mechanism exists.
- **Dispatch audit, then resume to apply** when a subagent mechanism exists and the scan is heavy enough to belong out of the main session: dispatch all three sub-agents in parallel in audit mode (read-only, each returning only its ranked findings record from `rules.md`), present them with their severity, take the user's selection, then resume with the selected findings as an upper bound — not a work order: `rules.md`: Apply re-proves each finding and drops it with reason when proof fails. Nothing the user did not select is applied. Reusing the scan context avoids re-exploring the repo; the consent gate stays in the main session. When the harness cannot resume agents, apply in the main session per `rules.md`: Apply. Never hand an audit findings list to a fresh agent as a fix order — that skips independent proof.
- If you cannot state the scope explicitly in the dispatch prompt, resolve it inline first — an ambiguous subagent dispatch silently falls back to the default scope.

## Execute

Read [`rules.md`](rules.md) in this skill's directory and execute every section in order. Include this skill directory's absolute path in every dispatch prompt so the agent reads `rules.md` from there.
