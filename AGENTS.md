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
Source (single truth)     →  _dist/ (only platform-specific)  →  Plugin loads / Script deploys
rules/common/*.md              _dist/cursor/rules/**/*.mdc       .cursor-plugin (skills→./skills/, agents→./agents/)
rules/{java,python,react}/     _dist/claude/rules/**/*.md        .claude-plugin (skills省略扫根, agents→./agents/*.md, mcp)
mcp.json (_platforms tag)      _dist/codex/AGENTS.md             .codex-plugin (skills→./skills/, mcp)
global-instructions.md         _dist/codex/mcp.json
skills/      ──────────────────┐  (all 3 platforms scan repo-root skills/ directly;
agents/*.md  ──────────────────┘   NOT copied into _dist/ — root is committed
                                  real files only, no vendor symlinks to break)
vendor/mattpocock-skills/  (manual install only → ~/.agents/skills/, not in _dist)
vendor/anysearch-skill/    (manual install only → ~/.claude+~/.agents/skills/, not in _dist)
```

`_dist/` now holds only what genuinely differs per platform: `mcp.json`
(`_platforms` filter), `rules/` (`.mdc` vs `.md`), and the global-instructions
deploy (`CLAUDE.md` / `AGENTS.md`). Skills and agents are read directly from the
repo root by all three platforms — no per-platform copy.

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

## anysearch-skill (manual install exception)

[anysearch-ai/anysearch-skill](https://github.com/anysearch-ai/anysearch-skill) is the **ONE skill that bypasses plugin distribution**, on purpose. It is a CLI skill (calls `api.anysearch.com`, NOT an MCP server) that replaces the former `exa` MCP server (removed from `mcp.json`). It is pinned at `vendor/anysearch-skill/` (submodule, tag `v2.1.0`) and installed manually via `install.py manual` (symlinks into `~/.claude/skills/` + `~/.agents/skills/`), never entering the repo-root `skills/` that the three platforms scan.

**Why not plugin-distributed?** The skill needs `runtime.conf` (agent-written at first use, picks python3/node/bash) and an optional `.env` (`ANYSEARCH_API_KEY`) to persist across sessions. But plugin cache (`~/.claude/plugins/cache/.../`) is a **read-only snapshot overwritten on every `ref: main` pull** (see Update Mechanism) — any file the agent writes there is lost on the next session. So anysearch installs as user-level symlinks outside the plugin cache, where each platform follows the symlink and persistent files survive.

**Install (all three platforms):**

```bash
uv run install.py manual           # install all manual skills
uv run install.py manual anysearch # install just this one
```

This subcommand is config-driven: it reads plugins in `third-party.json` that declare a top-level `install` object (`source` submodule path + `links` list of user-level paths) and symlinks each link → source. Adding a second manual skill means adding a `install` object to its `third-party.json` entry — no code change in `install.py`. For anysearch the declared links cover all three platforms' user-level skill paths (per each platform's official docs):

| symlink | read by | official source |
|---|---|---|
| `~/.claude/skills/anysearch` | Claude Code | Claude skills doc — `~/.claude/skills/` is Claude's ONLY user-level path. Claude does NOT scan `~/.agents/skills/`. |
| `~/.agents/skills/anysearch` | Codex (standard) + Cursor (standard) | Codex `loader.rs` — `~/.agents/skills` is the standard User scope (`~/.codex/skills` is deprecated legacy); Cursor skills doc — scans `~/.agents/skills/` and `~/.cursor/skills/`. |

Both links point at the same submodule, so a submodule update flows to all platforms at once. On first use the agent probes the runtime and writes `runtime.conf` inside the skill dir per `SKILL.md`. For higher rate limits set `ANYSEARCH_API_KEY` via env var or `<skill_dir>/.env` — anonymous access works without a key.

**Cursor caveat:** Cursor has a known bug where home-dir skill symlinks (`~/.agents/skills/`, `~/.cursor/skills/`) may vanish from the Skills panel after restart (unfixed as of v2.5.x). If hit, replace the `~/.agents/skills/anysearch` symlink with a copied folder for Cursor only (Codex follows symlinks correctly and needs no such workaround).

**Upgrade:** `git submodule update --remote vendor/anysearch-skill` (then re-pin to a release tag). The symlinks need no update — they point at the submodule, so content changes flow through automatically.

**This is the sole exception to "Single Source of Truth = this repo's plugin."** Do not add more skills to `~/.claude/skills/` or `~/.agents/skills/` manually — if a skill can be plugin-distributed, it goes in `skills/` and through `install.py build`. A manual skill is appropriate only when it needs persistent runtime files the plugin cache cannot hold; declare it in `third-party.json` with an `install` object and install via `install.py manual`.

## mattpocock/skills (hybrid management)

Engineering skills from [mattpocock/skills](https://github.com/mattpocock/skills), aligned to the 22 skills declared in upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json`. **Hybrid management** because mattpocock ships only a Claude native plugin (no Codex/Cursor plugin):

- **Claude Code**: provided by the native plugin `mattpocock-skills@mattpocock`. NOT in the repo-root `skills/` that Claude scans.
- **Codex / Cursor**: NOT in repo-root `skills/` either. Installed manually via `install.py manual mattpocock-skills`, which reads the upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json` skill list and symlinks each into `~/.agents/skills/` (the standard user-level path both Codex and Cursor scan). The submodule stays at `vendor/mattpocock-skills/` and never touches repo-root `skills/` — build runs `_clean_mattpocock_skill_symlinks` to remove any stale `skills/<name>` links left from older builds, keeping the root `skills/` clean (the single source all three platforms scan).

Trade-off vs the old build-deep-copy: submodule updates now flow to Codex/Cursor immediately (`git submodule update --remote` → symlinks point at new content, no rebuild/republish needed), but Codex/Cursor users must run `install.py manual` once after cloning. See Cursor caveat below.

### Included Skills (22, aligned to upstream plugin.json)

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

Claude gets mattpocock skills from its native plugin — nothing to do there. Codex/Cursor install via the manual subcommand, which is **generate-driven**: it reads the upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json` `skills` list and symlinks each into `~/.agents/skills/`. Adding/removing a skill upstream needs no code change here — re-running the subcommand picks up the new list.

```bash
# Install all 22 mattpocock skills into ~/.agents/skills/ (Codex + Cursor)
uv run install.py manual mattpocock-skills

# Update to upstream latest (symlinks point at the submodule, so content
# flows through automatically — no rebuild needed for Codex/Cursor)
git submodule update --remote vendor/mattpocock-skills
# then re-pin to a release tag in .gitmodules / git add vendor/mattpocock-skills
```

**Cursor caveat (same as anysearch):** home-dir skill symlinks may vanish from the Skills panel after restart (known v2.5.x bug). If hit, replace the affected `~/.agents/skills/<name>` symlinks with copied folders for Cursor only; Codex follows symlinks correctly.

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
3. **`source: "./"` 时 plugin 根 = clone 根 = 仓库根**，Cursor 会整树安全扫描。前提是仓库根在 fresh clone（不 init submodule）下**零含 `..` 的 symlink**。历史上 mattpocock 曾在 `skills/<name>` 建 vendor symlink（含 `..`、且 fresh clone 不 init submodule 会断链）触发 unsafe；现已改手动安装（`~/.agents/skills/`），根 `skills/` 只剩 committed 实目录，零 symlink。build 的 `_clean_mattpocock_skill_symlinks` 仍会清理本地残留旧 symlink 防污染。`_dist/` 不再拷 skills/agents（三平台都扫根）。
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

Claude's manifest schema differs from Cursor/Codex in two fields that `install.py build` keeps in sync with the repo root (not `_dist/` — skills/agents are no longer copied there):

- **`agents`** accepts only **file paths** (string|array), NOT a directory (unlike `skills` which accepts a directory). A directory value fails `claude plugin validate` with `agents: Invalid input` and the whole plugin fails to load. So `_sync_claude_manifest_agents()` enumerates the root `agents/*.md` into the `./agents/<name>` array after build. The committed value is `[]` (placeholder); build fills it.
- **`skills`** is deliberately **omitted**. Per schema it *adds to* the default `skills/` scan, so setting it would duplicate. Claude scans the plugin-root `skills/` instead, which holds only the 15 self-owned skills (mattpocock/anysearch are manual-installed elsewhere, not symlinked into root `skills/`).

## Key Files

- `install.py` - Build + deploy script (subcommands: `build`, `install`, `version`, `manual`)
- `global-instructions.md` - Deployed as `~/.claude/CLAUDE.md` and embedded in `~/.codex/AGENTS.md`
- `rules/common/*.md` - Always-on rules for all platforms
- `rules/{java,python,react}/*.md` - Language-specific rules with paths/globs
- `agents/*.md` - Subagent definitions (YAML frontmatter: name, description, model, tools)
- `skills/<name>/SKILL.md` - Agent skill definitions (15 self-owned, committed real dirs; scanned directly by all 3 platforms, NOT copied into `_dist/`)
- `vendor/mattpocock-skills/` - Git submodule of mattpocock/skills
- `vendor/anysearch-skill/` - Git submodule of anysearch-ai/anysearch-skill (manual install only, excluded from `_dist`)
- `mcp.json` - `_platforms` field for per-platform MCP server filtering
- `third-party.json` - Third-party plugin references (not bundled)
