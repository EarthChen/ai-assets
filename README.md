# earthchen-ai-assets

个人统一 AI Agent 资产管理仓库。一处维护，全平台同步。

## 支持平台

| 平台 | 插件加载 | 脚本补充 |
|------|---------|---------|
| Cursor | rules, skills, MCP | 仅 symlink |
| Claude Code | skills | rules → `~/.claude/rules/`, CLAUDE.md |
| Codex | skills | AGENTS.md + rules, approval rules |

## 目录结构

```
ai-plugins/
├── global-instructions.md     # 全局基础指令 (部署为 CLAUDE.md / AGENTS.md)
├── rules/                     # 共享规则 (部署到所有平台)
│   ├── KarpathyGuide.md       # Karpathy 12 Rules
│   ├── likaifuGuide.md        # Epistemic Auditor
│   ├── mcp-feedback-protocol.md  # platforms: [cursor]
│   └── codex-approval.rules   # Codex 命令审批规则
├── skills/                    # 共享技能 (所有平台可用)
│   ├── api-design/
│   ├── backend-patterns/
│   └── ...  (24 skills)
├── agents/                    # Subagent 定义 (Cursor + Claude)
│   ├── ecc-architect.md
│   ├── ecc-code-reviewer.md
│   └── ...  (34 agents)
├── mcp.json                   # 统一 MCP 配置 (_platforms 过滤)
├── _dist/                     # 自动生成的平台产物 (已提交)
│   ├── cursor/                # rules/ + skills + agents + mcp.json
│   ├── claude/                # rules/ + skills + agents + mcp.json + CLAUDE.md
│   └── codex/                 # skills + mcp.json + AGENTS.md
├── third-party.json           # 三方插件清单
├── .cursor-plugin/plugin.json
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
├── install.py                 # 一键安装脚本
├── AGENTS.md                  # 本项目开发指令
├── CLAUDE.md → AGENTS.md      # symlink
└── pyproject.toml
```

## 安装

```bash
# 全平台安装（生成 _dist/ + 部署）
uv run install.py

# 仅特定平台
uv run install.py --platform cursor

# 预览
uv run install.py --dry-run
```

> `_dist/` 已提交到 git，clone 后插件可直接使用，无需先运行脚本。
> 修改 `rules/` 或 `mcp.json` 后运行 `uv run install.py` 重新生成。

## 架构原则

**优先使用各平台原生插件系统，脚本仅处理插件无法覆盖的部分。**

| 平台 | 插件系统管理 | 脚本补充 |
|------|-------------|---------|
| Cursor | rules, skills, MCP | 仅创建 symlink |
| Claude Code | skills, MCP | rules, CLAUDE.md |
| Codex | skills | AGENTS.md, approval rules |

### 平台过滤机制

通过 YAML frontmatter 的 `platforms` 字段标记平台归属：

```yaml
---
description: "Only for Cursor"
alwaysApply: true
platforms: [cursor]
---
```

- 无 `platforms` 字段 → 所有平台共享
- `platforms: [cursor]` → 仅 Cursor 加载（脚本部署时自动跳过其他平台）

MCP 配置中使用 `_platforms` 字段：
```json
{
  "mcp-feedback-pro": {
    "command": "uvx",
    "args": ["mcp-feedback-pro@latest"],
    "_platforms": ["cursor"]
  }
}
```

### 为什么 Plugin Manifest 声明不同组件？

避免跨平台污染：
- **Cursor plugin** 声明 `rules + skills + agents + mcp` — 全功能
- **Claude plugin** 声明 `skills + agents + mcp` — rules 不支持插件分发
- **Codex plugin** 声明 `skills` — agents/rules 不支持

### 平台过滤（统一机制）

所有资产类型（rules, skills, agents, MCP）都支持 `platforms` 标记：

| 资产类型 | 标记位置 | 格式 |
|---------|---------|------|
| Rules | YAML frontmatter | `platforms: [cursor]` |
| Skills | `SKILL.md` frontmatter | `platforms: [cursor, claude]` |
| Agents | Agent `.md` frontmatter | `platforms: [cursor]` |
| MCP | JSON 字段 | `"_platforms": ["cursor"]` |

无标记 = 全平台共享。构建时自动过滤：
- 有过滤项 → 逐个 symlink（精确控制）
- 无过滤项 → 整目录 symlink（零开销）

## 三方插件

三方插件不包含在本仓库中，通过各平台原生插件系统独立管理：

- **superpowers**: Claude Code / Codex / Cursor 均可用
- **ECC**: Claude Code / Cursor (提供 agents, commands, 语言专属 rules)
- **understand-anything**: 通过 `~/.agents/skills/` symlink 引用

安装命令见 `third-party.json`。

## 新增规则/技能

1. 在 `rules/` 添加规则（Markdown + YAML frontmatter）
2. 在 `skills/<name>/SKILL.md` 添加技能
3. 如需限定平台，在 frontmatter 加 `platforms: [cursor]`
4. 运行 `uv run install.py` 同步
5. 重启 agent 生效
