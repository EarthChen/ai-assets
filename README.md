# ai-assets

个人统一 AI Agent 资产管理仓库。一处维护，全平台同步。

## 支持平台

| 平台 | 插件加载 | 脚本补充 |
|------|---------|---------|
| Cursor | rules, skills, agents, MCP | 仅 symlink |
| Claude Code | skills, agents, MCP | common rules → `~/.claude/rules/common/`, CLAUDE.md |
| Codex | skills, MCP | AGENTS.md (global-instructions + common rules) |

## 目录结构

```
ai-assets/
├── global-instructions.md     # 全局基础指令 (部署为 CLAUDE.md / AGENTS.md)
├── rules/                     # 共享规则 (按子目录分类)
│   ├── common/                # 通用规则 (所有平台/项目始终加载)
│   │   ├── common-coding-style.md
│   │   ├── KarpathyGuide.md
│   │   └── ...
│   ├── java/                  # Java 规则 (paths: **/*.java)
│   ├── python/                # Python 规则 (globs: **/*.py)
│   └── react/                 # React 规则 (globs: **/*.tsx)
├── skills/                    # 共享技能 (自有 + symlinked from vendor)
├── agents/                    # Subagent 定义 (Cursor + Claude)
├── vendor/                    # 第三方 git submodules
│   └── mattpocock-skills/     # mattpocock/skills 工程技能库
├── mcp.json                   # 统一 MCP 配置 (_platforms 过滤)
├── _dist/                     # 自动生成的平台产物 (已提交)
│   ├── cursor/                # rules/*.mdc + skills + agents + mcp.json
│   ├── claude/                # rules/ + skills + agents + mcp.json + CLAUDE.md
│   └── codex/                 # skills + mcp.json + AGENTS.md
├── .cursor-plugin/plugin.json
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
├── install.py                 # 一键安装脚本
├── AGENTS.md                  # 本项目开发指令
└── third-party.json           # 三方插件清单
```

## 安装

```bash
# 全平台 build + install（默认行为）
uv run install.py

# 仅特定平台
uv run install.py --platform cursor

# 预览
uv run install.py --dry-run
```

### 子命令

```bash
# 仅重建 _dist/（修改 rules/skills/mcp.json 后）
uv run install.py build

# 仅安装 symlinks（新机器 / _dist/ 已是最新）
uv run install.py install --platform cursor

# 版本管理
uv run install.py version              # 查看当前版本
uv run install.py version 1.2.0        # 设定指定版本
uv run install.py version --bump patch # 递增版本号 (major/minor/patch)
```

> `_dist/` 已提交到 git，clone 后插件可直接使用，无需先运行脚本。
> 修改 `rules/`、`skills/`、`agents/` 或 `mcp.json` 后运行 `uv run install.py build` 重新生成。

## 更新机制

| 平台 | 更新方式 | 说明 |
|------|---------|------|
| Cursor | 符号链接（即时） | build 后即生效，无需重启 |
| Codex | 符号链接（即时） | build 后即生效，无需重启 |
| Claude Code | ref-tracked 自动拉取 | 每次 session 启动自动从 GitHub main 分支拉取最新 |

### Claude Code 更新说明

`marketplace.json` 使用 `ref: "main"` 而非 SHA 固定：
- 无需手动 `claude plugin update`
- 无需管理 commit SHA（无鸡生蛋问题）
- 推送到 main → 下次启动 Claude Code 时自动生效
- 如需固定版本（生产环境），可在 `marketplace.json` 中添加 `sha` 字段

## 架构原则

**优先使用各平台原生插件系统，脚本仅处理插件无法覆盖的部分。**

| 平台 | 插件系统管理 | 脚本补充 |
|------|-------------|---------|
| Cursor | rules, skills, agents, MCP | 仅创建 symlink |
| Claude Code | skills, agents, MCP | common rules, CLAUDE.md |
| Codex | skills, MCP | AGENTS.md (含 common rules) |

### 单一配置源原则

本仓库是所有自定义 AI 配置的唯一来源。各平台不应有额外自定义配置：
- 不在 `~/.agents/skills/` 中手动放置 skill
- 不安装与本仓库功能重叠的第三方插件
- 第三方 skills（如 mattpocock/skills）：Claude 走原生插件安装；Codex/Cursor 通过 git submodule + vendor 分发
- MCP 服务器统一在本仓库 `mcp.json` 中管理

### mattpocock/skills（混合管理）

来自 [mattpocock/skills](https://github.com/mattpocock/skills) 的 21 个工程技能，对齐上游 [plugin.json](https://github.com/mattpocock/skills/blob/main/.claude-plugin/plugin.json) 的 skills 清单。采用**混合模式**分发，因 mattpocock 仓库只发布了 Claude 原生插件（无 Codex/Cursor 插件）：

| 平台 | 分发方式 | 说明 |
|------|---------|------|
| Claude Code | 原生插件 `mattpocock-skills@mattpocock` | 由上游插件提供，本仓库 build 时从 Claude 分发中排除，避免重复 |
| Codex | vendor submodule → deep copy 到 `_dist/codex/skills/` | 无上游 Codex 插件，由本仓库 build 分发 |
| Cursor | vendor submodule → deep copy 到 `_dist/cursor/skills/` | 无上游 Cursor 插件，由本仓库 build 分发 |

```bash
# Claude Code：原生插件由 install.py install 自动安装（配置在 third-party.json）
# 手动 fallback（安装失败时）：
#   claude plugin marketplace add mattpocock/skills
#   claude plugin install mattpocock-skills@mattpocock

# Codex/Cursor：_dist/ 已入库，clone 后可直接用；
# 仅在需要重新 build（修改 vendored skills 后）时才初始化 submodule
git submodule update --init

# 更新 vendor 到上游最新版本
git submodule update --remote vendor/mattpocock-skills
```

#### 推荐工作流

```
/grill-with-docs  →  需求对齐（深度询问 + 领域建模）
/to-spec          →  生成结构化 spec 文档
/to-tickets       →  拆解为可执行 ticket（本地 markdown 或 GitHub Issues）
/implement        →  按 ticket 顺序实现（TDD + code-review）
/code-review      →  双轴并行 review（Standards + Spec）
```

#### 技能清单（21 个，对齐上游 plugin.json）

| 分类 | 技能 | 说明 |
|------|------|------|
| **工作流** | `grill-with-docs` | Grilling + 领域建模 + CONTEXT.md / ADR |
| | `to-spec` | 将对话综合为 spec |
| | `to-tickets` | 拆解为 tracer-bullet 垂直切片 |
| | `implement` | 按 spec/ticket 实现，驱动 TDD + code-review |
| | `setup-matt-pocock-skills` | 项目一次性配置（issue tracker、domain docs） |
| | `triage` | issue 分类与优先级判断 |
| | `wayfinder` | 在复杂代码库中定位实现路径 |
| **核心能力** | `tdd` | Red-green-refactor + seam 测试 |
| | `diagnosing-bugs` | 6 阶段诊断法（含 feedback loop 构建） |
| | `code-review` | 双轴并行 subagent review |
| | `prototype` | 快速原型（logic 或 UI 两条路径） |
| | `research` | 后台 agent 研究 + 引用式 markdown |
| **设计** | `domain-modeling` | CONTEXT.md 术语表 + ADR 管理 |
| | `codebase-design` | 深模块设计词汇（module, seam, depth, adapter） |
| | `improve-codebase-architecture` | 架构扫描 + HTML 报告 + grilling |
| **通用** | `grilling` | 可复用的深度询问循环 |
| | `grill-me` | 用户触发的需求对齐面试 |
| | `handoff` | 跨 session 上下文传递 |
| | `teach` | 教学型技能编写与讲解 |
| | `writing-great-skills` | skill 编写规范与最佳实践 |
| | `ask-matt` | 向 Matt 提问的模板 |

#### 管理 Vendored Skills（仅影响 Codex/Cursor）

Claude 平台的 mattpocock skills 由原生插件提供，无需在此维护。下列命令仅调整 Codex/Cursor 分发的 symlink 清单：

```bash
# 添加新 skill（保持与上游 plugin.json 清单一致）
ln -s ../vendor/mattpocock-skills/skills/engineering/<name> skills/<name>
ln -s ../vendor/mattpocock-skills/skills/productivity/<name> skills/<name>

# 移除 skill
rm skills/<name>

# 更新后重建
uv run install.py build
```

### 各平台安装方式

| 平台 | 安装 | 更新 |
|------|------|------|
| Cursor | `~/.cursor/plugins/local/` symlink | build 后即时生效 |
| Codex | `~/.codex/plugins/local/` symlink + config.toml | build 后即时生效 |
| Claude Code | `claude plugin install` (GitHub URL) | 每次 session 自动拉取 main |

## Rules 系统详解

### 目录组织

```
rules/
├── common/     # 通用规则：始终加载，适用所有项目
├── java/       # 仅在编辑 Java 文件时加载
├── python/     # 仅在编辑 Python 文件时加载
└── react/      # 仅在编辑 React/TSX 文件时加载
```

### Frontmatter 格式（源文件统一格式）

```yaml
---
description: "规则描述"           # Cursor 用于智能选择
globs: ["**/*.py", "**/*.pyi"]   # 文件匹配模式 (Cursor/Claude)
paths:                           # 同 globs 的别名 (YAML 列表格式)
  - "**/*.java"
alwaysApply: true                # true=始终加载; false=条件加载
platforms: [cursor, claude]      # 平台过滤 (build-time, 不进入输出)
---
```

### 各平台 Frontmatter 转换

| 源字段 | Cursor (.mdc) | Claude Code (.md) | Codex (AGENTS.md) |
|--------|---------------|-------------------|--------------------|
| `description` | 保留 (Agent 智能选择) | 保留 | 无 (纯文本) |
| `paths` | → `globs` (JSON数组) | → `paths: CSV` (单行无引号) | N/A |
| `globs` | 保留 (JSON数组) | → `paths: CSV` (转换字段名) | N/A |
| `alwaysApply` | 保留 | 保留; paths 存在时自动加 false | N/A |
| `platforms` | **移除** | **移除** | N/A (build时过滤) |

### 各平台加载行为

| 规则类型 | Cursor | Claude Code | Codex |
|---------|--------|-------------|-------|
| **common/** (alwaysApply: true) | 始终加载 | 用户级始终加载 | 嵌入 AGENTS.md |
| **java/** (globs: \*\*.java) | 编辑 Java 文件时自动附加 | 项目级条件加载; 用户级不部署 | 不包含 |
| **python/** | 同上 (Python) | 同上 | 不包含 |
| **react/** | 同上 (React) | 同上 | 不包含 |

### 重要限制

1. **Cursor**: 必须使用 `globs`（不认 `paths`），规则扩展名必须为 `.mdc`
2. **Claude Code 用户级** (`~/.claude/rules/`): `paths` frontmatter 不生效 (Bug #21858)，规则始终无条件加载
3. **Claude Code 项目级** (`.claude/rules/`): `paths` 正常工作，可条件加载
4. **Codex**: 不支持 frontmatter，只认纯 Markdown；默认 32KB 限制

### Codex 32KB 限制

Codex `~/.codex/AGENTS.md` 默认限制 32KB (`project_doc_max_bytes`)。
本项目只嵌入 `rules/common/` (~20KB)，语言规则通过 Skills 按需提供。

如需调大：在 `~/.codex/config.toml` 设置 `project_doc_max_bytes = 131072`。

## 平台过滤机制

通过 YAML frontmatter 的 `platforms` 字段标记平台归属：

```yaml
---
platforms: [cursor]
---
```

- 无 `platforms` 字段 → 所有平台共享
- `platforms: [cursor]` → 仅 Cursor 加载
- `platforms: [cursor, claude]` → Cursor + Claude Code

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

### Plugin Manifest 声明

| 插件 | 组件 | 原因 |
|------|------|------|
| `.cursor-plugin` | rules, skills, agents, mcp | 全功能原生支持 |
| `.claude-plugin` | skills, agents, mcp | rules 需脚本部署 |
| `.codex-plugin` | skills, mcp | agents/rules 不支持 |

## 新增规则

1. 在 `rules/<category>/` 添加规则文件（`.md` + YAML frontmatter）
2. 通用规则放 `rules/common/`，语言规则放对应子目录
3. 语言规则需添加 `paths` 或 `globs` 字段指定文件匹配
4. 如需限定平台，添加 `platforms: [cursor, claude]`
5. 运行 `uv run install.py build` 重新生成 `_dist/`
6. 运行 `uv run install.py install` 部署
7. 重启 agent 生效

### 语言规则部署到项目

Claude Code 的语言规则需手动复制到项目才能条件加载：

```bash
# 复制 Java 规则到当前项目
cp -r _dist/claude/rules/java .claude/rules/
```

## 三方插件

三方插件记录在 `third-party.json` 中。mattpocock/skills 采用混合管理：Claude 走原生插件安装，Codex/Cursor 由本仓库 vendor（submodule）分发，不再依赖 superpowers 插件。
