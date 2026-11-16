---
name: agent-orchestration
description: "Use for architectural decisions, security-sensitive code, Java build breaks, or 2+ independent explore/review tasks: routes work to the right agent or skill."
---

# Agent Orchestration

Route work to the right agent or skill instead of doing it all inline. Planning, TDD, and code review run through workflow skills.

## Pick the workflow skill

Load model-invoked skills per the global "加载 Skill" rule, one skill per load: a step that needs two skills loads both.

| Need | Load the skill |
| --- | --- |
| Stress-test a plan or decision | `grilling` |
| Sharpen domain terms, glossary, ADRs | `domain-modeling` (with `grilling`: load both) |
| Build or fix test-first | `tdd` |
| Standards + Spec review of a diff | `code-review` (Claude Code name: `mattpocock-skills:code-review`, because the bare name also names a built-in) |

User-invoked skills (`/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`) fire only when the user types them. Tell the user to run them.

## Pick the agent

| Trigger | Agent |
| --- | --- |
| System-level architecture: design, scalability, trade-offs, ADR | `architect` |
| Feature-level "how this lands in existing code" blueprint | `code-architect` |
| Security-sensitive code (trigger list: `code-quality-gate` §4) | `code-reviewer` (its security lens) |
| Java/Maven/Gradle build failure | `java-build-resolver` |

Architect agents: `architect` for system-level depth, `code-architect` for feature-level speed.

## Pick the reviewer / simplifier

| Need | Use |
| --- | --- |
| Correctness bugs in a diff (Claude Code only) | built-in `/code-review` |
| Standards + Spec two-axis review of a diff | Load the mattpocock `code-review` skill (Claude Code name above) |
| Deep three-axis audit (Standards + Spec, language traps, cross-language lenses) | `code-reviewer` agent |
| Simplify changed code (Claude Code only) | built-in `/simplify` |
| Simplify changed code in one git scope | `code-simplifier` agent |
| Security review (all platforms; the single route) | `code-reviewer` agent (its security lens) |

Briefing context-heavy subagents: apply `references/iterative-retrieval.md` (dispatch → evaluate → refine, max 3 cycles) instead of guessing what context they need.

## Delegate only when it pays

This section is the single source for when to use a sub-agent. Model choice per sub-agent (Claude Code): the `claude-model-selection` rule. Pick the first row that matches:

1. **Split-role panel** (one sub-agent per role, dispatched in the same turn): reviewing a decision that is expensive to undo — architecture, data model, public API, security design. The roles are prompt roles, not agent files: factual reviewer, senior engineer, security expert, consistency reviewer, redundancy checker. The panel reviews a decision; to produce the design itself, use the `architect` agent (Pick the agent), then review its output with the panel.
2. **Inline**: a single lookup, a one-line edit, or a step whose result the next step needs and whose input fits in context.
3. **One sub-agent that returns a summary**: verbose reading (logs, search sweeps, large files). Keep the main context for decisions.
4. **One sub-agent per task, dispatched in the same turn**: 2+ independent explore / review / analysis tasks, each needing 3 or more tool calls.
5. **A lead with parallel workers**: only when the work is larger than one context window. A chain of dependent steps stays in one agent loop.

## Full agent catalogue

The complete list lives in `agents/*.md` — read it to discover `code-explorer`, `e2e-runner`, `performance-optimizer`, and the rest.
