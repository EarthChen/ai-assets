---
name: code-audit
disable-model-invocation: true
description: Deep, systematic code audit along three axes — Standards+Spec compliance, language-specific trap detection (Java/Python/TypeScript/FastAPI/PostgreSQL), and cross-language review lenses (silent failure, type design, security). For a quick diff review against general code smells, use the mattpocock code-review skill directly instead.
---

# Code Audit

Audit code along two axes: Standards+Spec compliance, and language-specific traps. The two axes are independent — a change can pass one and fail the other — so they run separately and report side by side, never merged or re-ranked.

## Choose The Mode

- "audit" / "deep review" → inspect only; return ranked findings per axis. Do not edit.
- "apply" / "fix" → implement the safest findings and verify them.

## Routing

Dispatch is justified by the scan's context weight, not by default — a single file audit is faster inline.

- **Run this skill inline** when the scope is one file or a trivial diff, findings need live discussion mid-pass, or no subagent mechanism exists.
- **Dispatch audit, then resume the same agent to apply** when a subagent mechanism exists and the scan is heavy enough to belong out of the main session: dispatch in audit mode (read-only, return only the ranked findings record from `rules.md`), present it, then resume the same agent with the approved findings as an upper bound — not a work order: it still proves each one per `rules.md` and rejects with reason when proof fails. **Consent is risk-gated on the audit's own classification**: all SAFE → resume directly, no human pause; any CAREFUL (dynamic imports / string-based references) or RISKY (public API surface, persisted format, compatibility path) → present it and take the user's selection before resuming. Reusing the scan context avoids re-exploring the repo; the consent gate stays in the main session.
- **Dispatch apply end-to-end** when the user pre-approved the scope or the harness cannot resume agents: one agent executes `rules.md` from audit through verify. Never hand an audit findings list to a fresh agent as a fix order — that skips independent proof.
- If you cannot state the scope explicitly in the dispatch prompt, resolve it inline first — an ambiguous subagent dispatch silently falls back to the default scope.

## Execute

The execution rules live in [`rules.md`](rules.md) in this skill's directory — Establish The Scope → Select Axes → Execute → Aggregate → Report. Read it and execute it end-to-end. Include this skill directory's absolute path in every dispatch prompt so the agent reads `rules.md` from there. The rules file is the single source of truth for both paths — never execute from memory.
