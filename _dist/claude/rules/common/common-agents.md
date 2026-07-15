---
description: "Agent orchestration: available agents, parallel execution, multi-perspective analysis"
alwaysApply: true
---
# Agent Orchestration

## Available Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| architect | System design | Architectural decisions |
| security-reviewer | Security analysis | Before commits |
| build-error-resolver | Fix build errors | When build fails |
| e2e-runner | E2E testing | Critical user flows |
| refactor-cleaner | Dead code cleanup | Code maintenance |
| doc-updater | Documentation | Updating docs |

> Planning, TDD, and code review are handled by the mattpocock/skills workflow
> (provided on Claude Code by the `mattpocock-skills@mattpocock` native plugin;
> vendored on Codex/Cursor), not by sub-agents:
> - **Planning** → `/grill-with-docs` → `/to-spec` → `/to-tickets` workflow chain
> - **TDD** → `/tdd` skill (red-green-refactor loop)
> - **Code review** → `/code-review` skill (dual-axis Standards + Spec review)

## Immediate Agent Usage

No user prompt needed:
1. Architectural decision - Use **architect** agent
2. Security-sensitive code - Use **security-reviewer** agent
3. Build failure - Use **build-error-resolver** agent

For planning / TDD / code review, invoke the mattpocock skills above instead.

## Parallel Task Execution

ALWAYS use parallel Task execution for independent operations:

```markdown
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: Security analysis of auth module
2. Agent 2: Performance review of cache system
3. Agent 3: Type checking of utilities

# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
