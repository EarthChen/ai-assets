# AI Plugins Repository

This repository manages unified AI agent assets across Claude Code, Codex, and Cursor.

## Development Guidelines

- Language: Chinese for communication, English for code/comments
- Package manager: `uv` for Python, `pnpm` for Node.js
- After modifying `rules/`, `skills/`, `agents/`, `mcp.json`, or `global-instructions.md`, run `uv run install.py build` to regenerate `_dist/`
- Commit `_dist/` changes along with source changes
- Bump version before release: `uv run install.py version --bump patch`

## Architecture

```
Source (single truth)     →  _dist/ (per-platform filtered)  →  Plugin loads / Script deploys
rules/common/*.md              _dist/cursor/rules/**/*.mdc       .cursor-plugin (all via plugin)
rules/{java,python,react}/     _dist/claude/rules/**/*.md        .claude-plugin (skills,agents,mcp)
mcp.json (_platforms tag)      _dist/codex/AGENTS.md             .codex-plugin (skills,mcp)
skills/ (own + vendored)       _dist/codex/mcp.json
vendor/mattpocock-skills/
agents/*.md
global-instructions.md
```

## Update Mechanism

| Platform | Method | Trigger |
|----------|--------|---------|
| Cursor | Marketplace (URL install) | Push to main → Cursor re-pulls on session |
| Codex | Local symlink (instant) | After `build` |
| Claude Code | ref-tracked auto-pull | Each session start (fetches main branch HEAD) |

Claude Code's `marketplace.json` uses `ref: "main"` without SHA pinning.
No manual `claude plugin update` needed; push to main → next session picks it up.

Cursor: `install.py install` no longer creates a `~/.cursor/plugins/local/`
symlink — Cursor's plugin registry only recognizes plugins installed via the
marketplace (each gets a numeric id in `state.vscdb`'s
`cursor.plugins.installedIds.*` keys; a local symlink is never counted, so it
silently failed to surface the plugin). Install via Settings → Customize →
add `https://github.com/EarthChen/ai-assets`. For dev preview only, manually
symlink this repo to `~/.cursor/plugins/local/` + Reload Window (not counted
in installedIds; marketplace install is the source of truth).

**Cursor "Include third-party Plugins, Skills, and other configs" (Settings →
Rules, Skills, Subagents): keep this OFF.** When on, Cursor recursively scans
`~/.claude/plugins/cache/*` (every version of this repo's Claude clone, each
with a full `skills/`), `~/.codex/skills/`, `~/.agents/skills/`, etc. with no
de-duplication, so every skill (e.g. `tdd`) loads ~11×. This is a known Cursor
bug (no ETA). Off is safe here because this repo's own `~/.claude/skills`,
`~/.codex/skills`, `~/.agents/skills` are essentially empty — the marketplace
install is the sole source.

## Single Source of Truth

This repo is the ONLY source for custom AI configuration:
- Do NOT place skills in `~/.agents/skills/` manually
- Do NOT install third-party plugins that overlap with this repo
- All MCP servers managed in this repo's `mcp.json`

## mattpocock/skills (hybrid management)

Engineering skills from [mattpocock/skills](https://github.com/mattpocock/skills), aligned to the 21 skills declared in upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json`. **Hybrid management** because mattpocock ships only a Claude native plugin (no Codex/Cursor plugin):

- **Claude Code**: provided by the native plugin `mattpocock-skills@mattpocock`. `install.py build` excludes these vendored skills from the Claude distribution so they aren't duplicated.
- **Codex / Cursor**: vendored as a git submodule at `vendor/mattpocock-skills/`, symlinked into `skills/`. Both deep-copy the resolved skill directories into `_dist/<platform>/skills/` at build (Codex → `_dist/codex/skills/`, Cursor → `_dist/cursor/skills/`). `_dist/` is committed, so both platforms work on clone without initializing the submodule.

After cloning, run `git submodule update --init` only if you need to rebuild `_dist/` (the committed `_dist/` already works without it).

### Included Skills (21, aligned to upstream plugin.json)

User-invoked (workflow chain):
- `grill-with-docs` → Grilling session + domain model / CONTEXT.md / ADRs
- `to-spec` → Synthesize conversation into structured spec
- `to-tickets` → Break spec into tracer-bullet tickets (supports local markdown)
- `implement` → Execute tickets with TDD + code-review
- `improve-codebase-architecture` → Architecture scan + HTML report + grilling
- `setup-matt-pocock-skills` → One-time project setup (issue tracker, domain docs)
- `grill-me` → Relentless interview to sharpen a plan or design
- `triage` → Move issues/external PRs through a triage state machine into agent-ready briefs
- `wayfinder` → Plan work too large for one session as a map of investigation tickets
- `ask-matt` → Router that picks which skill/flow fits your situation

Model-invoked (auto-selected by agent):
- `tdd` → Red-green-refactor loop with seam-based testing
- `diagnosing-bugs` → 6-phase diagnosis: feedback loop → reproduce → hypothesise → instrument → fix → cleanup
- `code-review` → Dual-axis (Standards + Spec) parallel sub-agent review
- `prototype` → Throwaway prototype (logic terminal app or UI variations)
- `research` → Background agent investigation with cited markdown output
- `domain-modeling` → Build/sharpen CONTEXT.md glossary and ADRs
- `codebase-design` → Deep module design vocabulary (module, interface, depth, seam, adapter)
- `grilling` → Core reusable interview loop

Productivity:
- `handoff` → Compact conversation into handoff document for another agent
- `teach` → Teach the user a new skill or concept within the workspace
- `writing-great-skills` → Reference for writing/editing skills well

### Managing Vendored Skills (Codex/Cursor only)

Claude gets mattpocock skills from its native plugin — no symlink maintenance needed there. The commands below only adjust the Codex/Cursor distribution. Keep the symlink set in sync with upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json`.

```bash
# Add a new mattpocock skill (match upstream plugin.json list)
ln -s ../vendor/mattpocock-skills/skills/engineering/<name> skills/<name>
ln -s ../vendor/mattpocock-skills/skills/productivity/<name> skills/<name>

# Remove a vendored skill
rm skills/<name>

# Update to upstream latest
git submodule update --remote vendor/mattpocock-skills

# After changes, rebuild
uv run install.py build
```

## Rules Deployment Strategy

| Platform | User-level (always loaded) | Language rules (conditional) |
|----------|---------------------------|------------------------------|
| Cursor | `rules/common/*.mdc` (alwaysApply: true) | Auto-attached via `globs` field |
| Claude Code | `~/.claude/rules/common/` (no frontmatter needed) | Project `.claude/rules/` (paths field) |
| Codex | Embedded in `~/.codex/AGENTS.md` (common only) | Via Skills on demand |

### Critical Platform Differences

- **Cursor**: uses `globs` field (NOT `paths`); extension must be `.mdc`
- **Claude Code user-level**: `paths` frontmatter is ignored (Bug #21858); rules always load unconditionally
- **Claude Code project-level**: `paths` works correctly for conditional loading
- **Codex**: no frontmatter support; 32KB limit on AGENTS.md; common rules only

### Cursor Plugin "Error loading plugin" — 根因与诊断

Cursor 插件加载失败的 UI 提示 "Error loading plugin" **不写进任何文件日志**，console 也只有 `getPluginMcpServers took Xms` 之类的性能 warn（零红色 error）。真实原因只藏在 UI 的 "Copy error details" 按钮剪贴板里。诊断顺序（踩过 7 轮坑的总结）：

1. **先读剪贴板错误，不要猜配置**。UI 卡片旁有 `aria-label="Copy error details"` 按钮，点击后用 `pbpaste` 读。本仓库命中的是：
   ```
   Unable to install plugin "earthchen-ai-assets" without gitPath:
   Plugin "earthchen-ai-assets" has unresolved or unsafe source path
   ```
2. **`unresolved or unsafe source path` = marketplace 的 `source` 解析出空 path**，不是 symlink 问题。Cursor 读 `.claude-plugin/marketplace.json`（和 Claude 同一个文件；ecc 连 `.cursor-plugin/` 都没有也照常加载）。`source` 必须是**字符串相对路径**（`"./"` 或 `"./_dist/cursor"`），写成 Claude 的对象格式 `{source:"url", url, ref}` 会让 Cursor 解析出 empty path → 把仓库根当 unsafe surface → 整个 plugin 失败 → skills/agents/rules/MCP 一个都不显示。
3. **`source: "./"` 时 plugin 根 = clone 根 = 仓库根**，Cursor 会整树安全扫描。前提是仓库根在 fresh clone（不 init submodule）下**零含 `..` 的 symlink**。所以下面的清理是 `source "./"` 能工作的必要前提，但单独做不解决 empty path：
   - 顶层 `skills/<name>` 的 mattpocock symlink 不能提交进 git（clone 不 init submodule → 断链 + 含 `..`）→ `.gitignore` 排除，由 `_ensure_mattpocock_skill_symlinks()` 在 build/install 时从上游 `plugin.json` 生成。
   - `_dist/claude/` 和 `_dist/cursor/` 的 skills/agents 必须深拷贝（`shutil.copytree`/`copy2`），不能用 symlink（`→ ../../skills` 含 `..`）。
4. **对照成功案例验证结构**：`~/.cursor/plugins/cache/cursor-public/superpowers/`（官方，加载成功）和 `~/.cursor/plugins/marketplaces/github.com/affaan-m/ecc/`（GitHub marketplace，`source: "./"`）。ecc 是最贴近本仓库的参照——同为 GitHub marketplace、`source: "./"`、根 skills 实目录、零含 `..` symlink。
5. **CDP 抓 console/剪贴板**：Cursor 带 `--remote-debugging-port=9333` 启动后，用 Cursor 自带的 `ws` 模块（`/Applications/Cursor.app/.../node_modules/ws`）连 `ws://127.0.0.1:9333/devtools/page/<id>`，`Runtime.evaluate` 点 `Copy error details` 按钮 + `pbpaste` 读系统剪贴板。`reload window` 不会 re-clone marketplace；要 re-clone 需完全退出 + 删 `~/.cursor/plugins/marketplaces/<host>/<owner>/<repo>/` + 重启。`fresh-clone`（`git clone --depth 1` 到 /tmp）可预先验证仓库根是否干净，不必反复发版。

### Build Transforms

| Source field | → Cursor | → Claude Code | → Codex |
|---|---|---|---|
| `paths: [...]` | `globs: [...]` (JSON array) | `paths: csv` (CSV string + alwaysApply: false) | stripped (plain text) |
| `globs: [...]` | kept as JSON array | → `paths: csv` (converted + alwaysApply: false) | stripped |
| `platforms: [...]` | removed | removed | used for filtering then stripped |
| `description` | kept | kept | stripped |
| `alwaysApply` | kept | kept | stripped |

### `.claude-plugin/plugin.json` manifest fields (build-synced)

Claude's manifest schema differs from Cursor/Codex in two fields that `install.py build` must keep in sync with `_dist/claude/`:

- **`agents`** accepts only **file paths** (string|array), NOT a directory (unlike `skills` which accepts a directory). A directory value fails `claude plugin validate` with `agents: Invalid input` and the whole plugin fails to load. So `_sync_claude_manifest_agents()` rewrites `agents` to the enumerated `./_dist/claude/agents/*.md` array after build. The committed value is `[]` (placeholder); build fills it.
- **`skills`** is deliberately **omitted**. Per schema it *adds to* the default `skills/` scan, so pointing it at `_dist/claude/skills/` would load every skill twice (root `skills/` + `_dist/claude/skills/`). Claude scans the plugin-root `skills/` instead, which on a marketplace clone contains only the 15 self-owned skills (the 21 mattpocock symlinks are `.gitignore`-excluded, provided by `mattpocock-skills@mattpocock`).

## Key Files

- `install.py` - Build + deploy script (subcommands: `build`, `install`, `version`)
- `global-instructions.md` - Deployed as `~/.claude/CLAUDE.md` and embedded in `~/.codex/AGENTS.md`
- `rules/common/*.md` - Always-on rules for all platforms
- `rules/{java,python,react}/*.md` - Language-specific rules with paths/globs
- `agents/*.md` - Subagent definitions (YAML frontmatter: name, description, model, tools)
- `skills/<name>/SKILL.md` - Agent skill definitions (own + symlinked from vendor)
- `vendor/mattpocock-skills/` - Git submodule of mattpocock/skills
- `mcp.json` - `_platforms` field for per-platform MCP server filtering
- `third-party.json` - Third-party plugin references (not bundled)
