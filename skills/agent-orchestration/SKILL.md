---
name: agent-orchestration
description: "Use for architectural decisions, security-sensitive code, build breaks, or 2+ independent explore/review tasks: routes work to the right agent or skill."
---

# Agent Orchestration

Route work to the right agent or skill instead of doing it all inline. Planning, TDD, and code review run through workflow skills: the model invokes `grilling`, `domain-modeling`, `tdd`, and the mattpocock `code-review` skill (`mattpocock-skills:code-review` on Claude) directly; `/grill-with-docs`, `/to-spec`, `/to-tickets`, and `/implement` are user-invoked — ask the user to run them.

## Pick the agent

| Trigger | Agent |
| --- | --- |
| System-level architecture: design, scalability, trade-offs, ADR | `architect` |
| Feature-level "how this lands in existing code" blueprint | `code-architect` |
| Security-sensitive code (auth, input, SQL, FS, crypto, payments) | `code-reviewer` (its security lens); on Claude Code, the built-in `/security-review` command also reviews pending changes |
| Java/Maven/Gradle build failure | `java-build-resolver` |
| Non-Java build failure | `build-error-resolver` |

Architect agents: `architect` for system-level depth, `code-architect` for feature-level speed.

## Pick the reviewer / simplifier

| Need | Use |
| --- | --- |
| Correctness bugs in a diff (Claude Code only) | built-in `/code-review` |
| Standards + Spec two-axis review of a diff | mattpocock `code-review` skill |
| Deep three-axis audit (Standards + Spec, language traps, cross-language lenses) | `code-reviewer` agent |
| Simplify changed code (Claude Code only) | built-in `/simplify` |
| Simplify changed code in one git scope | `code-simplifier` agent |
| Security review of pending changes (Claude Code only) | built-in `/security-review` |

Independent explore / review / analysis tasks: fan out per the global batch-first rule.

Briefing context-heavy subagents: apply `references/iterative-retrieval.md` (dispatch → evaluate → refine, max 3 cycles) instead of guessing what context they need.

## Delegate only when it pays

Reserve sub-agents for parallelizable or context-heavy work. Handle single lookups and one-line edits inline — sub-agent overhead outweighs the gain on small tasks.

## Split-role analysis (panel)

For complex problems, assign split-role sub-agents inline — these are prompt roles, not agent files:

- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker

## Full agent catalogue

The complete list lives in `agents/*.md` — read it to discover `code-explorer`, `e2e-runner`, `performance-optimizer`, and the rest.
