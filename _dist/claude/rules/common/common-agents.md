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

> Planning, TDD, and code review are handled by the mattpocock/skills workflow
> (provided on Claude Code by the `mattpocock-skills@mattpocock` native plugin;
> vendored on Codex/Cursor), not by sub-agents:
> - **Planning** → `/grill-with-docs` → `/to-spec` → `/to-tickets` workflow chain
> - **TDD** → `/tdd` skill (red-green-refactor loop)
> - **Code review** → `/code-review` skill (dual-axis Standards + Spec review)

### Architect Agents — 边界

仓库有两个软件架构 agent，按层级选用：

| Agent | Model | 职责边界 |
|-------|-------|---------|
| `architect` | opus | **系统级架构**：整体系统设计、可扩展性、技术决策、权衡分析、ADR。输出高层架构图 + 组件职责 + 数据模型 + API 契约。用于"做架构决策"。 |
| `code-architect` | sonnet | **特性级实现蓝图**：分析现有代码的模式和约定，给出具体文件路径 + 接口 + 数据流 + 构建顺序。用于"这个功能在现有代码里怎么落地"。 |

> 完整 agent 列表见 `agents/*.md`（含 java-reviewer / python-reviewer / typescript-reviewer / fastapi-reviewer / database-reviewer / mle-reviewer / performance-optimizer / spec-miner / code-explorer / code-simplifier / silent-failure-hunter / type-design-analyzer / harness-optimizer / loop-operator / marketing-agent 等），按需调用。

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

For complex problems, use split role sub-agents (these are **prompt roles**, not agent files — assign them inline to Task agents, do not look for `ecc-*.md` definitions):
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
