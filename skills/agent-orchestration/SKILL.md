---
name: agent-orchestration
description: "Use for architectural decisions, security-sensitive code, build breaks, or 2+ independent explore/review tasks: routes work to the right agent or skill."
---

# Agent Orchestration

Route work to the right agent or skill instead of doing it all inline. Planning, TDD, and code review run through workflow skills.

## Pick the workflow skill

Model-invoked skills load through the Skill tool. Each call takes one skill: a step that needs two skills is two calls.

| Need | Call the Skill tool with |
| --- | --- |
| Stress-test a plan or decision | `"grilling"` |
| Sharpen domain terms, glossary, ADRs | `"domain-modeling"` (with `"grilling"`: call the Skill tool twice) |
| Build or fix test-first | `"tdd"` |
| Standards + Spec review of a diff | `"mattpocock-skills:code-review"` on Claude (the bare `"code-review"` also names a built-in, so the namespaced name pins the target); `"code-review"` elsewhere |

User-invoked skills (`/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`) fire only when the user types them. Tell the user to run them.

## Pick the agent

| Trigger | Agent |
| --- | --- |
| System-level architecture: design, scalability, trade-offs, ADR | `architect` |
| Feature-level "how this lands in existing code" blueprint | `code-architect` |
| Security-sensitive code (trigger list: `code-quality-gate` §4) | `code-reviewer` (its security lens) |
| Java/Maven/Gradle build failure | `java-build-resolver` |
| Non-Java build failure | `build-error-resolver` |

Architect agents: `architect` for system-level depth, `code-architect` for feature-level speed.

## Pick the reviewer / simplifier

| Need | Use |
| --- | --- |
| Correctness bugs in a diff (Claude Code only) | built-in `/code-review` |
| Standards + Spec two-axis review of a diff | Call the Skill tool with the mattpocock `code-review` name (above) |
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
