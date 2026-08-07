---
name: agent-orchestration
description: "Agent & skill routing: architect (system) vs code-architect (feature) boundaries, security review, build failures, parallel subagent fan-out, split-role analysis. Use when an architectural decision, security-sensitive code, a build break, or several independent explore/review tasks land on you."
---

# Agent Orchestration

Route work to the right agent or skill instead of doing it all inline. Planning, TDD, and code review run through the mattpocock/skills workflow (`/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`, `/tdd`, `/code-review`) — reach for those skills directly.

## Pick the agent

| Trigger | Agent |
| --- | --- |
| System-level architecture: design, scalability, trade-offs, ADR | `architect` |
| Feature-level "how this lands in existing code" blueprint | `code-architect` |
| Security-sensitive code (auth, input, SQL, FS, crypto, payments) | `security-reviewer` |
| Build failure (any language / toolchain) | `build-error-resolver` |

Architect agents: `architect` for system-level depth, `code-architect` for feature-level speed.

Several independent explore / review / analysis tasks → launch them in one message (parallel fan-out), never sequentially.

## Delegate only when it pays

Reserve sub-agents for parallelizable or context-heavy work. Handle single lookups and one-line edits inline — sub-agent overhead outweighs the gain on small tasks.

## Split-role analysis (panel)

For complex problems, assign split-role sub-agents inline — these are prompt roles, not `ecc-*.md` files:

- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker

## Full agent catalogue

The complete list lives in `agents/*.md` — read it to discover java-reviewer, python-reviewer, fastapi-reviewer and the rest.
