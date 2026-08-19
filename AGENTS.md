# AI Plugins Repository

Unified AI agent assets across Claude Code, Codex, and Cursor. Single source of truth for skills, agents, rules, MCP.

## Development Guidelines

- Language: Chinese for communication, English for code/comments
- Package manager: `uv` for Python, `pnpm` for Node.js
- After modifying `rules/`, `skills/`, `agents/`, `mcp.json`, or `global-instructions.md`, run `uv run install.py build` to regenerate `_dist/`
- Commit `_dist/` changes along with source changes
- **Release = edit → `build` (if `_dist/` changed) → commit → `install`** (reinstall refreshes Claude's snapshot; version bump is optional, diagnostic only — see Update Mechanism)

## Architecture

```text
Source (single truth)     →  _dist/ (only platform-specific)  →  Plugin loads / Script deploys
rules/common/*.md              _dist/cursor/rules/**/*.mdc       .cursor-plugin (skills→./skills/, agents→./agents/)
rules/{common,java,python}/    _dist/claude/rules/**/*.md        .claude-plugin (skills省略扫根, agents→./agents/*.md, mcp)
mcp.json (_platforms tag)      _dist/codex/AGENTS.md             .codex-plugin (skills→./skills/, mcp)
global-instructions.md         _dist/codex/mcp.json
skills/      ──────────────────┐  (all 3 platforms scan repo-root skills/ directly;
agents/*.md  ──────────────────┘   NOT copied into _dist/ — root is committed
                                  real files only, no vendor symlinks to break)
pi/skills/ + pi/agents/ ─────── pi only (install_pi symlinks into ~/.pi/agent/{skills,agents}/;
                                  invisible to Claude/Codex/Cursor)
vendor/mattpocock-skills/   (symlink-installed → ~/.agents/skills/, not in _dist)
vendor/anysearch-skill/     (symlink-installed → ~/.claude+~/.agents/skills/, not in _dist)
vendor/understand-anything/ (symlink-installed → ~/.agents+~/.claude/skills/, not in _dist)
vendor/herdr-skill/         (symlink-installed → ~/.agents+~/.claude/skills/, not in _dist)
```

`_dist/` holds only what genuinely differs per platform: `mcp.json` (`_platforms` filter), `rules/` (`.mdc` vs `.md`), and the global-instructions deploy (`CLAUDE.md` / `AGENTS.md`). Skills and agents are read directly from the repo root by all three platforms — no per-platform copy.

## pi support (script-only deploy)

[pi](https://github.com/badlogic/pi-mono) has no plugin system compatible with this repo, so `install.py install --platform pi` deploys directly to `~/.pi/agent/`:

- **AGENTS.md**: `_dist/pi/AGENTS.md` (global-instructions + common rules, same embed as Codex; pi loads it from `~/.pi/agent/` at startup — no 32KB limit) → `~/.pi/agent/AGENTS.md`, **full overwrite** (repo is the single source of truth; my-pi-agent's own project docs live in that repo's CLAUDE.md)
- **Skills**: self-owned skills symlinked into `~/.agents/skills/` — pi scans that standard directory natively; same mechanism as the mattpocock/anysearch manual installs (which therefore need no extra work). Not registered via `settings.json`. Note: Codex also scans `~/.agents/skills/`, so it sees these links in addition to its plugin copy
- **pi-only skills**: `pi/skills/*` symlinked into `~/.pi/agent/skills/` — pi scans that dir recursively and no other harness scans it (unlike `~/.agents/skills/`, which Codex also reads), so these skills load exclusively on pi. Currently: none (`herdr-orchestration` moved to root `skills/` — it went multi-platform: orchestrator AND workers can run on pi, Claude Code, or Codex, mixed pools allowed)
- **Agents**: `agents/*.md` symlinked into `~/.pi/agent/agents/` — pi-subagents' `discoverAgents()` scans that user dir (alongside its builtins scout/reviewer/worker/...) and loads `*.md` with YAML frontmatter. Repo agent frontmatter only sets `name` + `description`; `model` and `tools` are intentionally omitted so pi-subagents inherits the parent session's model and grants the default tool set. Verify with `/subagents-doctor` + `subagent({ action: "list" })` after install.
- **pi-only agents**: `pi/agents/*.md` symlinked into the same `~/.pi/agent/agents/` dir — the Claude manifest sync (`_sync_claude_manifest_agents`) enumerates only `agents/`, so these load exclusively on pi. Currently: `Explore.md`
- **NOT deployed**: MCP (pi covers playwright etc. via its own extensions — no `mcp.json` sync), separate rules files (embedded in AGENTS.md; language rules via skills on demand)

## Update Mechanism

| Platform | Method | Trigger |
| ---------- | -------- | --------- |
| Cursor | `install.py install` (rsync real-dir, `--delete`) | After repo edits + restart/reload |
| Codex | Local symlink (instant, tracks repo) | After `build` |
| Claude Code | `install.py install` (local-directory marketplace, reinstall = fresh snapshot) | After `build` (when `_dist/` changed); bump optional |
| pi | `install.py install --platform pi` (direct deploy to `~/.pi/agent/`) | After `build` + install |

**Claude Code is version-gated.** This repo's marketplace is registered as a **local directory** (`marketplace_source: "local"` in `third-party.json` → `install.py install` runs `claude plugin marketplace add <REPO_ROOT>`), not a git remote — so `plugin update` reads the working tree directly, no `git fetch`/`push` round-trip. But the version check is unchanged: Claude compares `plugin.json`'s `version` field against the installed snapshot; same version → it reports "already at latest" and skips the re-snapshot, even when the working tree has changed. So the update flow is **edit → `build` (if `_dist/claude/` changed) → `install.py install --platform claude`** (reinstall forces a fresh snapshot — `uninstall`+`install` under the hood, bypassing the version skip). Optionally bump `plugin.json`+`marketplace.json` version for diagnostic clarity (cache dir + `plugin list` reflect the real content). Verified: at 1.1.0, content changes without a version bump left the cache at the old snapshot with deleted agents still present; `install.py install`'s reinstall path fixes this. Bump **both** `plugin.json` and `marketplace.json` together if you bump at all — Claude reads `plugin.json` version for the update decision (marketplace.json's version alone is not enough).

**When a bump is NOT needed:** version-gating only governs content that lives in the plugin cache snapshot Claude pulls on `plugin update` — i.e. repo-root `skills/`, `agents/`, `.mcp.json`, and the `CLAUDE.md`/`AGENTS.md` body embedded into `_dist/claude/`. Third-party (manual/symlink) skills — mattpocock, understand-anything, anysearch, herdr — live as symlinks in `~/.claude/skills/` (user-level), which Claude scans directly and which **never pass through the plugin cache**. So edits to `install.py`, `third-party.json`, `third-party.schema.json`, or the vendor submodules do NOT require a version bump to surface on Claude; on any machine just run `uv run install.py install` (or `install.py manual <name>`) to (re)create the symlinks. The version-gating check is: did `_dist/claude/` (the cached plugin payload) actually change? If `git status _dist/` is clean after `build`, no bump is needed for Claude.

**Local vs remote marketplace:** this repo defaults to a local-directory marketplace (`marketplace_source: "local"` in `third-party.json`; `install.py install` runs `marketplace add <REPO_ROOT>`) — no `git push` needed to update Claude's cache, just `build` + `install.py install` (reinstall). The remote-git marketplace path still works for fresh machines that haven't cloned the repo: `claude plugin marketplace add https://github.com/EarthChen/ai-assets.git` then `plugin install` (version-gated `plugin update` on refresh). Third-party plugins without `marketplace_source` default to `remote` (git clone, version-gated `plugin update`). Codex (symlink tracks repo) and Cursor (rsync `--delete` re-copies) are NOT version-gated — `install.py install` and they pick up new content.

Cursor local plugin: copied as a **real directory** (not symlink) to `~/.cursor/plugins/local/earthchen-ai-assets`. Cursor's local-plugin scanner skips symlinks in that dir (verified Cursor 2.5.x: symlinked plugin dir is never indexed, skills never load). Codex keeps a symlink — its scanner follows symlinks fine. Restart Cursor or Developer: Reload Window after install.

**Cursor marketplace has a stale-cache problem** (parallel alternative only): Cursor resolves a marketplace to a commit SHA on first import and caches it — does NOT re-resolve on reinstall or session start (reinstalling keeps pulling the first-imported commit). So marketplace installs get stuck on the first-imported version. For reliable updates use `install.py install` (local real-dir). `cursor` CLI has no `plugin` subcommand, so marketplace install is UI-only (Settings → Customize → add `https://github.com/EarthChen/ai-assets`). Local + marketplace same name → double-load (duplicate skills); pick one, prefer local.

**Cursor "Include third-party Plugins, Skills, and other configs" (Settings → Rules, Skills, Subagents): keep OFF.** When ON, Cursor recursively scans `~/.claude/plugins/cache/*` (every version of this repo's Claude clone, each with full `skills/`), `~/.codex/skills/`, `~/.agents/skills/` with no de-duplication → every skill (e.g. `tdd`) loads ~11×. Known Cursor bug (no ETA). OFF is safe here because this repo's own `~/.claude/skills`, `~/.codex/skills`, `~/.agents/skills` are empty — the repo-root `skills/` is the sole source.

## Single Source of Truth

This repo is the ONLY source for custom AI configuration:

- Do NOT place skills in `~/.agents/skills/` manually
- Do NOT install third-party plugins that overlap with this repo
- All MCP servers managed in this repo's `mcp.json`

## third-party skills (symlink-installed, bypass plugin cache)

Four third-party skill sets are **NOT plugin-distributed** — they install as user-level symlinks so their runtime files (`runtime.conf`, `.env`, upstream-pinned content) survive outside the plugin cache (a read-only snapshot overwritten on every version pull). All four are declared in `third-party.json` with a top-level `install` object and deployed by `install.py`'s manual-skill path, which **`install.py install` runs automatically** (no separate `install.py manual` needed):

| Skill set | submodule | discovery | links |
| --- | --- | --- | --- |
| **mattpocock-skills** | `vendor/mattpocock-skills` | `generate.from+field` (reads upstream `plugin.json` skills list, 25 skills) | `~/.agents/skills/` |
| **understand-anything** | `vendor/understand-anything` | `generate.scan_dir` (scans `understand-anything-plugin/skills/` for SKILL.md subdirs, 11 skills — upstream `plugin.json` has no skills list) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **anysearch** | `vendor/anysearch-skill` | `links` (explicit list, single skill) | `~/.claude/skills/anysearch` + `~/.agents/skills/anysearch` |
| **herdr** | `vendor/herdr-skill` | `generate.scan_dir` (scans `skills/` — sparse submodule pinned to the single herdr skill) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |

**context-mode** also has a `third-party.json` entry, but it is a **provenance record only**: not a skill distributed by this repo — installed per-platform via each platform's native plugin/npm path (Claude: `install.py` auto-runs `claude plugin marketplace add mksglu/context-mode` + `plugin install context-mode@context-mode --scope user`). The entry formalizes the ctx-* tools this repo's docs reference.

`install.py manual <name>` remains as a single-skill reinstall entry point. All three platforms (Claude, Codex, Cursor) follow these symlinks correctly; no per-platform workaround needed. Adding a third-party skill = adding a `third-party.json` entry with an `install` object (choose `links` for single-skill repos, `generate.from+field` if upstream declares a skill list, `generate.scan_dir` if it doesn't) — no `install.py` code change. See `third-party.schema.json` for the `install`/`installConfig`/`generateConfig` schema.

### anysearch-skill

[anysearch-ai/anysearch-skill](https://github.com/anysearch-ai/anysearch-skill) is a CLI skill (calls `api.anysearch.com`, NOT an MCP server) replacing the former `exa` MCP server. Pinned at `vendor/anysearch-skill/` (submodule).

**Why not plugin-distributed?** The skill needs `runtime.conf` (agent-written at first use) and optional `.env` (`ANYSEARCH_API_KEY`) to persist across sessions. But plugin cache (`~/.claude/plugins/cache/.../`) is a **read-only snapshot overwritten on every version pull** — files the agent writes there are lost next session. So anysearch installs as user-level symlinks outside the plugin cache, where persistent files survive.

**Upgrade:** `git submodule update --remote vendor/anysearch-skill` (re-pin to a release tag). Symlinks need no update — content flows through automatically.

### understand-anything

[EarthChen/Understand-Anything](https://github.com/EarthChen/Understand-Anything) — AI-powered codebase understanding: analyze, visualize, and explain any project via an interactive knowledge graph. Submodule at `vendor/understand-anything`; 11 skills under `understand-anything-plugin/skills/<name>/SKILL.md` plus a `shared/` lib dir (not a skill, skipped by `scan_dir`). Upstream `plugin.json` carries no `skills` list, so discovery uses `generate.scan_dir`.

Not plugin-distributed for the same reason as anysearch: runtime files (`system.json`, generated graphs under `.understand-anything/`) must survive across sessions outside the read-only plugin cache.

**Upgrade:** `git submodule update --remote vendor/understand-anything` (re-pin to a tag if upstream tags one). Symlinks need no update — content flows through automatically.

### herdr-skill

The [herdr](https://github.com/badlogic/herdr) terminal-multiplexer control skill, pinned as a **sparse submodule** at `vendor/herdr-skill` (tracks upstream, checks out only the single skill). Same symlink distribution as the other sets; gives Claude/Codex/Cursor/pi the `herdr` CLI etiquette without vendoring the whole upstream repo.

**Upgrade:** `git submodule update --remote vendor/herdr-skill`. Symlinks flow automatically.

### mattpocock/skills

Engineering skills from [mattpocock/skills](https://github.com/mattpocock/skills). **Hybrid management** because mattpocock ships only a Claude native plugin (no Codex/Cursor plugin):

- **Claude Code**: provided by native plugin `mattpocock-skills@mattpocock`. NOT in repo-root `skills/`, NOT in `~/.claude/skills/`.
- **Codex / Cursor / pi**: symlinked into `~/.agents/skills/` by `install.py install` (or `install.py manual mattpocock-skills` to reinstall just this set). Reads the upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json` `skills` list (25 entries). Submodule stays at `vendor/mattpocock-skills/`, never touches repo-root `skills/`. Build runs `_clean_mattpocock_skill_symlinks` to remove stale `skills/<name>` links from older builds.

Trade-off vs old build-deep-copy: submodule updates now flow to Codex/Cursor immediately (`git submodule update --remote` → symlinks point at new content, no rebuild needed), but Codex/Cursor users must run `install.py install` once after cloning to create the symlinks (the main install now covers this — no separate `manual` command needed).

**25 skills** (full list with descriptions: `vendor/mattpocock-skills/.claude-plugin/plugin.json`). User-invoked workflow chain: `grill-with-docs` → `to-spec` → `to-tickets` → `implement` → `code-review`. Model-invoked: `tdd`, `diagnosing-bugs`, `research`, `domain-modeling`, `codebase-design`, `prototype`, `grilling`. Productivity: `handoff`, `teach`, `writing-for-agents`, `grill-me`, `to-questionnaire`, `wait-what`. Support: `resolving-merge-conflicts`, `wizard`. Routers: `ask-matt`, `wayfinder`, `triage`, `improve-codebase-architecture`, `setup-matt-pocock-skills`.

The manual path is **generate-driven**: reads the upstream `plugin.json` `skills` list and symlinks each. Adding/removing a skill upstream needs no code change here — re-running picks up the new list.

```bash
uv run install.py manual mattpocock-skills                              # install all 25
git submodule update --remote vendor/mattpocock-skills                  # update upstream (symlinks auto-flow)
# then re-pin to a release tag: git add vendor/mattpocock-skills
```

## Rules Deployment Strategy

| Platform | User-level (always loaded) | Language rules (conditional) |
| ---------- | --------------------------- | ------------------------------ |
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
| --- | --- | --- | --- |
| `paths: [...]` | `globs: [...]` (JSON array) | `paths: csv` (CSV string + alwaysApply: false) | stripped (plain text) |
| `globs: [...]` | kept as JSON array | → `paths: csv` (converted + alwaysApply: false) | stripped |
| `platforms: [...]` | removed | removed | used for filtering then stripped |
| `description` | kept | kept | stripped |
| `alwaysApply` | kept | kept | stripped |

### `.claude-plugin/plugin.json` manifest fields (build-synced)

Claude's manifest schema differs from Cursor/Codex in two fields that `install.py build` keeps synced with the repo root (not `_dist/` — skills/agents are no longer copied there):

- **`agents`** accepts only **file paths** (string|array), NOT a directory (unlike `skills` which accepts a directory). A directory value fails `claude plugin validate` with `agents: Invalid input` and the whole plugin fails to load. So `_sync_claude_manifest_agents()` enumerates the root `agents/*.md` into the `./agents/<name>` array after build; the synced array is committed alongside the build output so Claude's snapshot always lists the current agents.
- **`skills`** is deliberately **omitted**. Per schema it *adds to* the default `skills/` scan, so setting it would duplicate. Claude scans the plugin-root `skills/` instead, which holds only the self-owned skills (mattpocock/anysearch are manual-installed elsewhere, not symlinked into root `skills/`).
