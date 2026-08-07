---
name: agent-orchestration
description: "Route agent/skill work: architect boundaries, immediate agent usage, multi-perspective analysis. Use when deciding which agent or skill to invoke for architecture decisions, security review, build failures, or parallel subagent fan-out."
---

# Agent Orchestration

## When to Use

- You need to decide which architect agent (`architect` vs `code-architect`) fits a task.
- You are about to make an architectural decision, touch security-sensitive code, hit a build failure, or have multiple independent explore/review/analysis tasks.
- You want split-role (multi-perspective) analysis: factual reviewer, senior engineer, security expert, consistency reviewer, redundancy checker.
- Note: planning / TDD / code review are delegated to the mattpocock/skills workflow (`/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`, `/tdd`, `/code-review`), not to sub-agents.

> Planning, TDD, and code review are handled by the mattpocock/skills workflow
> (provided on Claude Code by the `mattpocock-skills@mattpocock` native plugin;
> vendored on Codex/Cursor), not by sub-agents:
>
> - **Planning → implementation** → `/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement` workflow chain
> - **TDD** → `/tdd` skill (red-green-refactor loop)
> - **Code review** → `/code-review` skill (dual-axis Standards + Spec review)

### Architect Agents — 边界

仓库有两个软件架构 agent，按层级选用：

| Agent | Model | 职责边界 |
| ------- | ------- | --------- |
| `architect` | opus | **系统级架构**：整体系统设计、可扩展性、技术决策、权衡分析、ADR。输出高层架构图 + 组件职责 + 数据模型 + API 契约。用于"做架构决策"。 |
| `code-architect` | sonnet | **特性级实现蓝图**：分析现有代码的模式和约定，给出具体文件路径 + 接口 + 数据流 + 构建顺序。用于"这个功能在现有代码里怎么落地"。 |

> 完整 agent 列表见 `agents/*.md`（含 java-reviewer / python-reviewer / typescript-reviewer / fastapi-reviewer / database-reviewer / performance-optimizer / code-explorer / code-simplifier / silent-failure-hunter / type-design-analyzer / harness-optimizer / loop-operator 等），按需调用。

## Immediate Agent Usage

No user prompt needed:

1. Architectural decision - Use **architect** agent
2. Security-sensitive code - Use **security-reviewer** agent
3. Build failure - Use **build-error-resolver** agent
4. Multiple independent exploration / review / analysis tasks - proactively split them across subagents and launch them in ONE message (parallel), instead of doing them sequentially yourself

Do NOT delegate single lookups or small edits — subagent overhead outweighs the gain.

For planning / TDD / code review, invoke the mattpocock skills above instead.

## Multi-Perspective Analysis

For complex problems, use split role sub-agents (these are **prompt roles**, not agent files — assign them inline to Task agents, do not look for `ecc-*.md` definitions):

- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
