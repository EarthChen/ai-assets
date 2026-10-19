# ai-assets

个人统一 AI Agent 资产管理仓库。一处维护，全平台同步。

> 仓库维护者文档：见 [CONTRIBUTING.md](CONTRIBUTING.md)（deploy 流水线、vendor 管理、build transforms、诊断步骤）。

## 支持平台

| 平台 | 插件加载 | 脚本补充 |
| ------ | --------- | --------- |
| Cursor | rules, agents, MCP | local real-dir (rsync，不含 `skills/`) + skills/ → `~/.agents/skills/` |
| Claude Code | skills, agents（软链到 `~/.claude/`） | `rules/common` → `~/.claude/rules/common`、`global-instructions.md` → `~/.claude/CLAUDE.md`（均为软链，无需 build） |
| Codex | — | AGENTS.md (global-instructions + common rules) + skills/ → `~/.agents/skills/` |
| pi | — | AGENTS.md + skills/ → `~/.agents/skills/`（与三方 symlink 同目录）+ pi/skills/ → `~/.pi/agent/skills/` + agents/ 与 pi/agents/ → `~/.pi/agent/agents/` |

## 目录结构

```text
ai-assets/
├── global-instructions.md     # 全局基础指令 (部署为 CLAUDE.md / AGENTS.md)
├── rules/                     # 共享规则 (仅 common/；语言规则已合并到 skills/)
│   └── common/                # 通用规则 (所有平台/项目始终加载)
│       ├── common-coding-style.md
│       ├── KarpathyGuide.md
│       └── ...
│   ├── (历史：java/、python/ 已合并到 skills/java-development/references/ 与 skills/python-development/references/)
├── skills/                    # 共享技能 (19 个自有实目录；vendor skills 由 install.py symlink 安装)
├── agents/                    # Subagent 定义 (Cursor + Claude + pi，12 个)
├── pi/                        # pi 专属资源: skills/ + agents/ → ~/.pi/agent/ (仅 pi 加载)
├── docs/                      # 团队分享文档（能力、设计依据与工作流）
├── site/                      # VitePress 文档站源码（GitHub Pages，CI 部署）
├── vendor/                    # 第三方 git submodules
│   ├── mattpocock-skills/     # mattpocock/skills 工程技能库 (27 skills)
│   ├── anysearch-skill/       # anysearch CLI 搜索技能
│   ├── understand-anything/   # 代码库知识图谱理解 (11 skills)
│   ├── herdr-skill/           # Herdr 终端复用器控制技能 (sparse submodule)
│   ├── playwright-cli/        # microsoft/playwright-cli 浏览器自动化技能
│   ├── humanlayer-skills/     # humanlayer/skills monorepo (链接 show-me + visual-pr)
│   └── yao-meta-skill/        # skill 工程元技能 (替代原 skill-creator)
├── mcp.json                   # 统一 MCP 配置 (_platforms 过滤)
├── _dist/                     # 自动生成的平台产物 (已提交；skills/agents 不复制进此)
│   ├── cursor/                # rules/*.mdc + mcp.json
│   ├── codex/                 # mcp.json + AGENTS.md
│   └── pi/                    # AGENTS.md
├── .cursor-plugin/plugin.json
├── .cursor-plugin/marketplace.json
├── .claude-plugin/marketplace.json  # Claude：仅指向 hooks/claude
├── hooks/claude/              # Claude 插件（仅 hooks）
├── install.py                 # 一键安装脚本
├── installer/                 # install.py 的实现（按阶段/平台分模块）
├── tests/                     # pytest（uv run pytest；含 _dist/ golden 测试）
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

`install.py install` 会自动完成三方 skills 的 symlink 安装（mattpocock / anysearch / understand-anything / herdr / playwright-cli / show-me / visual-pr / yao-meta-skill），无需单独运行 `manual`。

### 子命令

```bash
# 仅重建 _dist/（修改 rules/global-instructions.md/mcp.json 后）
uv run install.py build

# 仅安装 symlinks（新机器 / _dist/ 已是最新）
uv run install.py install --platform cursor

# 单个三方技能重装
uv run install.py manual <name>

# 版本管理
uv run install.py version              # 查看当前版本
uv run install.py version 1.2.0        # 设定指定版本
uv run install.py version --bump patch # 递增版本号 (major/minor/patch)
```

> `_dist/` 已提交到 git，clone 后插件可直接使用，无需先运行脚本。
> 修改 `rules/`、`global-instructions.md` 或 `mcp.json` 后运行 `uv run install.py build` 重新生成（`skills/`、`agents/` 不经过 build）；`uv run pytest` 会在 `_dist/` 过期时失败。

## 更新机制

| 平台 | 方法 | 触发 |
| -------- | ------ | -------- |
| Cursor | `install.py install`（rsync real-dir） | 修改后 + 重启 |
| Codex | 插件符号链接（skills 即时）；`~/.codex/AGENTS.md` 为副本 | skills 无需操作；AGENTS.md 需 build + install |
| Claude Code | `install.py install` (local-directory marketplace, reinstall) | 无需 bump，reinstall 即刷新 |
| pi | `install.py install --platform pi` | build + install |

> 详见 [CONTRIBUTING.md - Update Mechanism — Detailed](CONTRIBUTING.md#update-mechanism--detailed)：Claude version-gating、
> Cursor marketplace stale-cache 等踩坑记录。

## 架构原则

**优先使用各平台原生插件系统，脚本仅处理插件无法覆盖的部分。**

| 平台 | 插件系统管理 | 脚本补充 |
| ------ | ------------- | --------- |
| Cursor | rules, skills, agents, MCP | 复制仓库为 real-dir 本地插件（非 symlink） |
| Claude Code | skills, agents, MCP | common rules, CLAUDE.md |
| Codex | skills, MCP | AGENTS.md (含 common rules) |
| pi | —（无兼容插件系统） | AGENTS.md, skills/agents symlink 直接部署 |

### 单一配置源原则

本仓库是所有自定义 AI 配置的唯一来源。各平台不应有额外自定义配置：

- 不在 `~/.agents/skills/` 中手动放置 skill
- 不安装与本仓库功能重叠的第三方插件
- 第三方 skills（如 mattpocock/skills）：Claude 走原生插件安装；Codex/Cursor/pi 通过 git submodule + vendor symlink 分发
- MCP 服务器统一在本仓库 `mcp.json` 中管理

### mattpocock/skills（混合管理）

来自 [mattpocock/skills](https://github.com/mattpocock/skills) 的 27 个工程技能，对齐上游 [plugin.json](https://github.com/mattpocock/skills/blob/main/.claude-plugin/plugin.json) 的 skills 清单。采用**混合模式**分发，因 mattpocock 仓库只发布了 Claude 原生插件（无 Codex/Cursor 插件）：

| 平台 | 分发方式 | 说明 |
| ------ | --------- | ------ |
| Claude Code | 原生插件 `mattpocock-skills@mattpocock` | 由上游插件提供，不在 repo-root `skills/` |
| Codex / Cursor / pi | `install.py install` 自动 symlink 进 `~/.agents/skills/` | submodule 不进 `_dist/`，更新即时生效 |

```bash
# Claude Code：原生插件由 install.py install 自动安装（配置在 third-party.json）
# 手动 fallback（安装失败时）：
#   claude plugin marketplace add mattpocock/skills
#   claude plugin install mattpocock-skills@mattpocock

# Codex/Cursor/pi：clone 后运行一次 install.py install 创建 symlinks；
# symlinks 直接指向 vendor/，submodule 更新后无需重建
git submodule update --init

# 更新 vendor 到上游最新版本（symlinks 自动跟随）
git submodule update --remote vendor/mattpocock-skills
```

#### 推荐工作流

```text
/grill-with-docs  →  需求对齐（深度询问 + 领域建模）
/to-spec          →  生成结构化 spec 文档
/to-tickets       →  拆解为可执行 ticket（本地 markdown 或 GitHub Issues）
/implement        →  按 ticket 顺序实现（TDD + code-review）
/code-review      →  双轴并行 review（Standards + Spec）
```

#### 技能清单（27 个，对齐上游 plugin.json）

| 分类 | 技能 | 说明 |
| ------ | ------ | ------ |
| **工作流** | `grill-with-docs` | Grilling + 领域建模 + CONTEXT.md / ADR |
| | `to-spec` | 将对话综合为 spec |
| | `to-tickets` | 拆解为 tracer-bullet 垂直切片 |
| | `implement` | 按 spec/ticket 实现，驱动 TDD + code-review |
| | `setup-matt-pocock-skills` | 项目一次性配置（issue tracker、domain docs） |
| | `triage` | issue 分类与优先级判断 |
| | `wayfinder` | 在复杂代码库中定位实现路径 |
| | `implement-spec` | 落地 `/to-spec` + `/to-tickets` 的产出 |
| | `pr` | 撰写 PR 描述 |
| | `retro` | 编码 session 复盘 |
| **核心能力** | `tdd` | Red-green-refactor + seam 测试 |
| | `diagnosing-bugs` | 6 阶段诊断法（含 feedback loop 构建） |
| | `code-review` | 双轴并行 subagent review |
| | `prototype` | 快速原型（logic 或 UI 两条路径） |
| | `research` | 后台 agent 研究 + 引用式 markdown |
| | `wizard` | 交互式 bash 向导（引导仅人类可执行的步骤） |
| **设计** | `domain-modeling` | CONTEXT.md 术语表 + ADR 管理 |
| | `codebase-design` | 深模块设计词汇（module, seam, depth, adapter） |
| | `improve-codebase-architecture` | 架构扫描 + HTML 报告 + grilling |
| **通用** | `grilling` | 可复用的深度询问循环 |
| | `grill-me` | 用户触发的需求对齐面试 |
| | `handoff` | 跨 session 上下文传递 |
| | `teach` | 教学型技能编写与讲解 |
| | `writing-for-agents` | agent 消费文档（skills/AGENTS.md）写作规范 |
| | `ask-matt` | 向 Matt 提问的模板 |
| | `to-questionnaire` | 把无法立刻拍板的决策转成问卷，交给他人填写 |
| | `wait-what` | 叫停重来：上一条消息没被理解时，重新阐述上一轮提议 |

### 各平台安装方式

| 平台 | 安装 | 更新 |
| ------ | ------ | ------ |
| Cursor | `install.py install`（local real-dir，不含 `skills/`；skills 经 `~/.agents/skills/` symlink） | rsync `--delete` 重建，修改后重启 |
| Codex | `~/.agents/skills/` symlink + AGENTS.md（不再注册 repo 插件，install 会禁用旧注册） | skills 经 symlink 即时跟踪 repo；AGENTS.md 需 build + install |
| Claude Code | `install.py install`（`marketplace_source: "local"` → `marketplace add <REPO_ROOT>` + reinstall） | `install.py install` reinstall 即刷新；bump version 可选（诊断用） |
| pi | `install.py install --platform pi` | build + install |

## Rules 系统详解

语言专属规则（Java、Python）已合并到 `skills/java-development/references/` 与 `skills/python-development/references/`，由 skill description 触发加载。下面只讲通用 `rules/common/` 及其 frontmatter 机制。

### 目录组织

```text
rules/
└── common/     # 通用规则：始终加载，适用所有项目
```

新增通用规则：在 `rules/common/` 添加 `.md` 文件 + 写 YAML frontmatter（`description`、`alwaysApply: true` 可选）。

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

Claude Code 不经过 build：`rules/common` 整个目录软链，文件必须直接符合 Claude 的 frontmatter（`description`、`alwaysApply: true`；用户级 `paths` 不生效）。`rules/common` 中任何排除 claude 的规则会让 `build` 报错，平台专属规则放进 `rules/<platform>/`（如 `rules/cursor/`）。

| 源字段 | Cursor (.mdc) | Codex (AGENTS.md) |
| -------- | --------------- | -------------------- |
| `description` | 保留 (Agent 智能选择) | 无 (纯文本) |
| `paths` | → `globs` (JSON数组) | N/A |
| `globs` | 保留 (JSON数组) | N/A |
| `alwaysApply` | 保留 | N/A |
| `platforms` | **移除** | N/A (build时过滤) |

### 各平台加载行为

| 规则类型 | Cursor | Claude Code | Codex |
| --------- | -------- | ------------- | ------- |
| **common/** (alwaysApply: true) | 始终加载 | 用户级始终加载 | 嵌入 AGENTS.md |

语言规范不属于 rules：各平台按需从 `skills/<lang>-development/` 加载。

### 重要限制

1. **Cursor**: 必须使用 `globs`（不认 `paths`），规则扩展名必须为 `.mdc`
2. **Claude Code 用户级** (`~/.claude/rules/`): `paths` frontmatter 不生效 (Bug #21858)，规则始终无条件加载
3. **Claude Code 项目级** (`.claude/rules/`): `paths` 正常工作，可条件加载
4. **Codex**: 不支持 frontmatter，只认纯 Markdown；默认 32KB 限制

### Codex 32KB 限制

Codex `~/.codex/AGENTS.md` 默认限制 32KB (`project_doc_max_bytes`)。
本项目嵌入 `global-instructions.md` + `rules/common/`，当前共 12.6KB；语言规则通过 Skills 按需提供，不占常驻预算。组成细节见 `CONTRIBUTING.md` 的 Codex AGENTS.md 32KB Limit 一节。

如需调大：在 `~/.codex/config.toml` 设置 `project_doc_max_bytes = 131072`。

## 平台过滤机制

通过 YAML frontmatter 的 `platforms` 字段标记平台归属：

```yaml
---
platforms: [cursor]
---
```

- 无 `platforms` 字段 → 所有平台共享
- `platforms: [cursor]` → 仅 Cursor 加载，文件放在 `rules/cursor/`，**不能**放在 `rules/common/`（Claude 直接软链该目录，`build` 会报错）

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
| ------ | ------ | ------ |
| `.cursor-plugin` | rules, agents, mcp | skills 走 `~/.agents/skills/`，插件不重复提供 |
| `.claude-plugin` → `hooks/claude` | hooks | skills/agents/rules 走 `~/.claude` 软链部署，插件只补软链无法承载的 hooks |

## 新增规则

1. 在 `rules/common/` 添加规则文件（`.md` + YAML frontmatter，`alwaysApply: true`）
2. 平台过滤用 `platforms: [cursor, claude]`
3. 运行 `uv run install.py build` 重新生成 `_dist/`
4. 运行 `uv run install.py install` 部署
5. 重启 agent 生效

## 新增语言规则（Java / Python / 等）

语言规则放在 `skills/<lang>-development/references/` 而不是 `rules/<lang>/`，由 skill description 触发加载。增加新语言：新建 `skills/<lang>-development/` + 写 SKILL.md + 在 `references/` 里放主题文档；如有项目级语言规则仍可放 `rules/<lang>/` 并用 `globs`/`paths` 触发。

## 三方插件

三方插件记录在 `third-party.json` 中（schema 见 `third-party.schema.json`），`install.py install` 自动完成安装：

| 插件 | 形态 | 分发方式 |
| ------ | ------ | ------ |
| mattpocock-skills | Claude 原生插件 + vendor submodule | Claude 走原生插件；Codex/Cursor/pi symlink 进 `~/.agents/skills/` |
| anysearch | vendor submodule（CLI 技能） | symlink 进 `~/.claude/skills/` + `~/.agents/skills/` |
| understand-anything | vendor submodule（11 skills） | symlink 进 `~/.agents/skills/` + `~/.claude/skills/` |
| herdr | vendor submodule（sparse，单技能） | symlink 进 `~/.agents/skills/` + `~/.claude/skills/` |
| playwright-cli | vendor submodule（单技能） | symlink 进 `~/.agents/skills/` + `~/.claude/skills/` |
| show-me | vendor submodule（humanlayer monorepo，仅用户显式调用） | symlink 进 `~/.agents/skills/` + `~/.claude/skills/` |
| visual-pr | vendor submodule（humanlayer monorepo，PR 可视化描述） | symlink 进 `~/.agents/skills/` + `~/.claude/skills/` |
| yao-meta-skill | vendor submodule（单技能，仓库根即 skill） | symlink 进 `~/.claude/skills/` + `~/.agents/skills/` |
| context-mode | 仅溯源登记 | 不经本仓库分发；各平台原生插件/npm 安装（Claude 由 install.py 自动装） |

> symlink 安装绕过插件缓存，运行时文件（`runtime.conf`、生成的图谱等）得以跨 session 留存。
> 详细机制与踩坑记录见 [CONTRIBUTING.md - Third-Party Skills](CONTRIBUTING.md#third-party-skills-symlink-installed)。

## 文档站点

`site/` 为 VitePress 文档站（GitHub Pages 部署，CI 见 `.github/workflows/deploy-pages.yml`）：

```bash
pnpm install
pnpm docs:dev      # 本地预览
pnpm docs:build    # 构建
```

## License

MIT（`package.json` 声明）。仓库暂无 `LICENSE` 文件 [待填：是否补交 LICENSE 文件]。
