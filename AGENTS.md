# AI Plugins Repository

Unified AI agent assets across Claude Code, Codex, and Cursor. Single source of truth for skills, agents, rules, MCP.

## Development Guidelines

- Language: Chinese for communication, English for code/comments
- Package manager: `uv` for Python, `pnpm` for Node.js
- After modifying `rules/`, `skills/`, `agents/`, `mcp.json`, or `global-instructions.md`, run `uv run install.py build` to regenerate `_dist/`
- Commit `_dist/` changes along with source changes
- **Release = bump version → build → commit → push → install** (see Update Mechanism: Claude is version-gated, bump is mandatory)

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

`_dist/` holds only what genuinely differs per platform: `mcp.json` (`_platforms` filter), `rules/` (`.mdc` vs `.md`), and the global-instructions deploy (`CLAUDE.md` / `AGENTS.md`). Skills and agents are read directly from the repo root by all three platforms — no per-platform copy.

## Update Mechanism

| Platform | Method | Trigger |
|----------|--------|---------|
| Cursor | `install.py install` (rsync real-dir, `--delete`) | After repo edits + restart/reload |
| Codex | Local symlink (instant, tracks repo) | After `build` |
| Claude Code | `claude plugin update` (pulls marketplace `ref: main`) | **Version-gated — see below** |

**Claude Code is version-gated.** `marketplace.json`'s `version` field is the ONLY signal Claude uses to decide whether to pull new content. Pushing to `main` without bumping version → `claude plugin update` sees the same version in cache and skips → cache stays at the old content (verified: pushed agent deletions + global rewrite at 1.1.0, but cache remained old 1.1.0 with the deleted agents still present). So the release flow is **bump version → build → commit → push → install**; skip the bump and Claude does not update. Codex (symlink tracks repo) and Cursor (rsync `--delete` re-copies) are NOT version-gated — push + install and they pick up new content.

Cursor local plugin: copied as a **real directory** (not symlink) to `~/.cursor/plugins/local/earthchen-ai-assets`. Cursor's local-plugin scanner skips symlinks in that dir (verified Cursor 2.5.x: symlinked plugin dir is never indexed, skills never load). Codex keeps a symlink — its scanner follows symlinks fine. Restart Cursor or Developer: Reload Window after install.

**Cursor marketplace has a stale-cache problem** (parallel alternative only): Cursor resolves a marketplace to a commit SHA on first import and caches it — does NOT re-resolve on reinstall or session start (reinstalling keeps pulling the first-imported commit). So marketplace installs get stuck on the first-imported version. For reliable updates use `install.py install` (local real-dir). `cursor` CLI has no `plugin` subcommand, so marketplace install is UI-only (Settings → Customize → add `https://github.com/EarthChen/ai-assets`). Local + marketplace same name → double-load (duplicate skills); pick one, prefer local.

**Cursor "Include third-party Plugins, Skills, and other configs" (Settings → Rules, Skills, Subagents): keep OFF.** When ON, Cursor recursively scans `~/.claude/plugins/cache/*` (every version of this repo's Claude clone, each with full `skills/`), `~/.codex/skills/`, `~/.agents/skills/` with no de-duplication → every skill (e.g. `tdd`) loads ~11×. Known Cursor bug (no ETA). OFF is safe here because this repo's own `~/.claude/skills`, `~/.codex/skills`, `~/.agents/skills` are empty — the repo-root `skills/` is the sole source.

## Single Source of Truth

This repo is the ONLY source for custom AI configuration:
- Do NOT place skills in `~/.agents/skills/` manually
- Do NOT install third-party plugins that overlap with this repo
- All MCP servers managed in this repo's `mcp.json`

## anysearch-skill (manual install exception)

[anysearch-ai/anysearch-skill](https://github.com/anysearch-ai/anysearch-skill) is the **ONE skill that bypasses plugin distribution**, on purpose. CLI skill (calls `api.anysearch.com`, NOT an MCP server) replacing the former `exa` MCP server. Pinned at `vendor/anysearch-skill/` (submodule, tag `v2.1.0`), installed manually via `install.py manual` (symlinks into `~/.claude/skills/` + `~/.agents/skills/`), never entering repo-root `skills/`.

**Why not plugin-distributed?** The skill needs `runtime.conf` (agent-written at first use) and optional `.env` (`ANYSEARCH_API_KEY`) to persist across sessions. But plugin cache (`~/.claude/plugins/cache/.../`) is a **read-only snapshot overwritten on every version pull** — files the agent writes there are lost next session. So anysearch installs as user-level symlinks outside the plugin cache, where persistent files survive.

```bash
uv run install.py manual           # install all manual skills
uv run install.py manual anysearch # install just this one
```

The subcommand is config-driven: reads `third-party.json` entries with a top-level `install` object (`source` submodule path + `links` list of user-level paths) and symlinks each link → source. Adding a manual skill = adding an `install` object to its `third-party.json` entry, no code change in `install.py`. Both links point at the same submodule, so a submodule update flows to all platforms at once.

**Cursor caveat:** home-dir skill symlinks may vanish from the Skills panel after restart (known v2.5.x bug). If hit, replace the `~/.agents/skills/anysearch` symlink with a copied folder for Cursor only (Codex follows symlinks correctly).

**Upgrade:** `git submodule update --remote vendor/anysearch-skill` (re-pin to a release tag). Symlinks need no update — content flows through automatically.

**Sole exception to "Single Source of Truth = this repo's plugin."** Do not add more skills to `~/.claude/skills/` or `~/.agents/skills/` manually — if a skill can be plugin-distributed, it goes in `skills/` and through `install.py build`. A manual skill is appropriate only when it needs persistent runtime files the plugin cache cannot hold; declare it in `third-party.json` with an `install` object.

## mattpocock/skills (hybrid management)

Engineering skills from [mattpocock/skills](https://github.com/mattpocock/skills). **Hybrid management** because mattpocock ships only a Claude native plugin (no Codex/Cursor plugin):

- **Claude Code**: provided by native plugin `mattpocock-skills@mattpocock`. NOT in repo-root `skills/`.
- **Codex / Cursor**: installed manually via `install.py manual mattpocock-skills`, which reads the upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json` skill list and symlinks each into `~/.agents/skills/`. Submodule stays at `vendor/mattpocock-skills/`, never touches repo-root `skills/`. Build runs `_clean_mattpocock_skill_symlinks` to remove stale `skills/<name>` links from older builds.

Trade-off vs old build-deep-copy: submodule updates now flow to Codex/Cursor immediately (`git submodule update --remote` → symlinks point at new content, no rebuild needed), but Codex/Cursor users must run `install.py manual` once after cloning. Same Cursor symlink caveat as anysearch (may vanish after restart → copy folders for Cursor only).

**22 skills** (full list with descriptions: `vendor/mattpocock-skills/.claude-plugin/plugin.json`). User-invoked workflow chain: `grill-with-docs` → `to-spec` → `to-tickets` → `implement` → `code-review`. Model-invoked: `tdd`, `diagnosing-bugs`, `research`, `domain-modeling`, `codebase-design`, `prototype`, `grilling`. Productivity: `handoff`, `teach`, `writing-great-skills`. Routers: `ask-matt`, `wayfinder`, `triage`, `improve-codebase-architecture`, `setup-matt-pocock-skills`, `grill-me`.

The manual subcommand is **generate-driven**: reads the upstream `plugin.json` `skills` list and symlinks each. Adding/removing a skill upstream needs no code change here — re-running picks up the new list.

```bash
uv run install.py manual mattpocock-skills                              # install all 22
git submodule update --remote vendor/mattpocock-skills                  # update upstream (symlinks auto-flow)
# then re-pin to a release tag: git add vendor/mattpocock-skills
```

## Rules Deployment Strategy

| Platform | User-level (always loaded) | Language rules (conditional) |
|----------|---------------------------|------------------------------|
| Cursor | `rules/common/*.mdc` (alwaysApply: true) | Auto-attached via `globs` field |
| Claude Code | `~/.claude/rules/common/` (no frontmatter needed) | Project `.claude/rules/` (paths field) |
| Codex | Embedded in `~/.codex/AGENTS.md` (common only, 32KB limit) | Via Skills on demand |

### Critical Platform Differences

- **Cursor**: uses `globs` field (NOT `paths`); extension must be `.mdc`
- **Claude Code user-level**: `paths` frontmatter is ignored (Bug #21858); rules always load unconditionally
- **Claude Code project-level**: `paths` works correctly for conditional loading
- **Codex**: no frontmatter support; 32KB limit on AGENTS.md; common rules only

### Cursor Plugin "Error loading plugin" — 诊断

UI 提示 "Error loading plugin" **不写进任何文件日志**，console 也只有性能 warn。真实原因只藏在 UI "Copy error details" 按钮的剪贴板里。诊断顺序（踩过 7 轮坑的总结）：

1. **先读剪贴板错误，不要猜配置**：点 UI 卡片旁 `aria-label="Copy error details"` 按钮，`pbpaste` 读。本仓库命中过 `Unable to install plugin without gitPath: Plugin has unresolved or unsafe source path`。
2. **`unresolved or unsafe source path` = marketplace `source` 解析出空 path**。`.claude-plugin/marketplace.json` 的 `source` 必须是字符串相对路径（`"./"` 或 `"./_dist/cursor"`），写成 Claude 的对象格式 `{source,url,ref}` 会让 Cursor 解析出 empty path → 整个 plugin 失败 → skills/agents/rules/MCP 一个都不显示。
3. **`source: "./"` 时 plugin 根 = clone 根 = 仓库根**，前提是仓库根在 fresh clone（不 init submodule）下**零含 `..` 的 symlink**。历史 mattpocock 曾在 `skills/<name>` 建 vendor symlink（含 `..`、fresh clone 断链）触发 unsafe；现已改手动安装，根 `skills/` 只剩 committed 实目录。build 的 `_clean_mattpocock_skill_symlinks` 清理本地残留。
4. **对照成功案例**：`~/.cursor/plugins/cache/cursor-public/superpowers/`（官方）和 `~/.cursor/plugins/marketplaces/github.com/affaan-m/ecc/`（`source: "./"`）。
5. **CDP 抓 console/剪贴板**：Cursor 带 `--remote-debugging-port=9333` 启动，用 Cursor 自带 `ws` 模块连 devtools，`Runtime.evaluate` 点 Copy error details + `pbpaste`。`reload window` 不 re-clone marketplace；要 re-clone 需完全退出 + 删 `~/.cursor/plugins/marketplaces/<host>/<owner>/<repo>/` + 重启。`fresh-clone`（`git clone --depth 1` 到 /tmp）可预先验证仓库根是否干净。

### Build Transforms

| Source field | → Cursor | → Claude Code | → Codex |
|---|---|---|---|
| `paths: [...]` | `globs: [...]` (JSON array) | `paths: csv` (CSV string + alwaysApply: false) | stripped (plain text) |
| `globs: [...]` | kept as JSON array | → `paths: csv` (converted + alwaysApply: false) | stripped |
| `platforms: [...]` | removed | removed | used for filtering then stripped |
| `description` | kept | kept | stripped |
| `alwaysApply` | kept | kept | stripped |

### `.claude-plugin/plugin.json` manifest fields (build-synced)

Claude's manifest schema differs from Cursor/Codex in two fields that `install.py build` keeps synced with the repo root (not `_dist/` — skills/agents are no longer copied there):

- **`agents`** accepts only **file paths** (string|array), NOT a directory (unlike `skills` which accepts a directory). A directory value fails `claude plugin validate` with `agents: Invalid input` and the whole plugin fails to load. So `_sync_claude_manifest_agents()` enumerates the root `agents/*.md` into the `./agents/<name>` array after build. The committed value is `[]` (placeholder); build fills it.
- **`skills`** is deliberately **omitted**. Per schema it *adds to* the default `skills/` scan, so setting it would duplicate. Claude scans the plugin-root `skills/` instead, which holds only the self-owned skills (mattpocock/anysearch are manual-installed elsewhere, not symlinked into root `skills/`).

## Key Files

- `install.py` - Build + deploy script (subcommands: `build`, `install`, `version`, `manual`)
- `global-instructions.md` - Deployed as `~/.claude/CLAUDE.md` and embedded in `~/.codex/AGENTS.md`
- `rules/common/*.md` - Always-on rules for all platforms
- `rules/{java,python,react}/*.md` - Language-specific rules with paths/globs
- `agents/*.md` - Subagent definitions (YAML frontmatter: name, description, model, tools)
- `skills/<name>/SKILL.md` - Agent skill definitions (scanned directly by all 3 platforms, NOT copied into `_dist/`)
- `vendor/mattpocock-skills/` - Git submodule of mattpocock/skills
- `vendor/anysearch-skill/` - Git submodule of anysearch-ai/anysearch-skill (manual install only, excluded from `_dist`)
- `mcp.json` - `_platforms` field for per-platform MCP server filtering
- `third-party.json` - Third-party plugin references (not bundled)
