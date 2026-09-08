# Contributing to ai-assets

Maintenance guide for the ai-assets repo itself. End-user product documentation lives in `README.md` and `AGENTS.md`; this file covers the deploy pipeline, build mechanics, vendor submodule management, and踩坑 knowledge that only repo maintainers need.

## When to Read This File

- Adding or modifying rules, skills, agents, or MCP servers
- Bumping plugin versions
- Debugging a broken `_dist/` build
- Updating vendor submodules
- Diagnosing "Error loading plugin" in Cursor / Claude Code
- Understanding why `_dist/` exists and what's synced vs not

## Architecture: Source vs Dist

The repo has two layers:

1. **Source (single truth)** — `rules/`, `skills/`, `agents/`, `mcp.json`, `global-instructions.md`, `install.py`, `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `third-party.json`
2. **`_dist/` (per-platform outputs, committed)** — `cursor/`, `claude/`, `codex/`, `pi/`

`install.py build` regenerates `_dist/` from source. Skills and agents are **not** copied into `_dist/` — all three platforms scan the repo root `skills/`/`agents/` directly. `_dist/` holds only what genuinely differs per platform:

- `mcp.json` (`_platforms` filter)
- `rules/` (`.mdc` vs `.md` + frontmatter transform)
- `global-instructions.md` deploy (becomes `CLAUDE.md` / `AGENTS.md`)

Why commit `_dist/`? Fresh clones work without running the install script. Cursor and Codex don't need a build step; Claude Code users run `install.py install` to refresh from the committed `_dist/claude/`.

### Plugin Manifest Sync (`_dist/claude/plugin.json`)

`install.py build` calls `_sync_claude_manifest_agents()` to keep two manifest fields synced with the repo root:

- **`agents`** accepts only file paths (string|array), NOT a directory. A directory value fails `claude plugin validate` with `agents: Invalid input` and the whole plugin fails to load. Build enumerates `agents/*.md` into the `./agents/<name>` array; the synced array is committed alongside the build output so Claude's snapshot always lists the current agents.
- **`skills`** is deliberately omitted. Per schema it *adds to* the default `skills/` scan, so setting it would duplicate. Claude scans the plugin-root `skills/` directly, which holds only the self-owned skills (mattpocock/anysearch are manual-installed elsewhere).

After adding/removing an agent, run `uv run install.py build` and commit the regenerated `plugin.json`.

## Build Transforms (rules frontmatter → per-platform)

| Source field | → Cursor (.mdc) | → Claude Code (.md) | → Codex (AGENTS.md) |
| --- | --- | --- | --- |
| `paths: [...]` | `globs: [...]` (JSON array) | `paths: csv` (CSV string + `alwaysApply: false`) | stripped (plain text) |
| `globs: [...]` | kept as JSON array | → `paths: csv` (converted + `alwaysApply: false`) | stripped |
| `platforms: [...]` | removed | removed | used for filtering then stripped |
| `description` | kept | kept | stripped |
| `alwaysApply` | kept | kept | stripped |

## Codex AGENTS.md 32KB Limit

Codex reads `~/.codex/AGENTS.md` under a 32KB ceiling (`project_doc_max_bytes`). `install.py build` composes that file from **`global-instructions.md` + every `rules/common/*.md` that passes the codex platform filter** (frontmatter stripped) → `_dist/codex/AGENTS.md` → deployed on install. Current size: 12.6KB (well under).

Repo-root `AGENTS.md` is **not** part of the embed — it is maintainer documentation only, so its length never touches the Codex budget. Moving text between `global-instructions.md` and `rules/common/` is likewise a no-op for size: both are embedded.

If you approach the limit, in order of preference:

1. Move detailed踩坑 knowledge out to CONTRIBUTING.md (this file) — not embedded
2. Demote an always-on `rules/common/*.md` into a skill reference, so it loads on demand instead of every turn — the same move the java/python rules just made
3. As last resort: raise `project_doc_max_bytes` in `~/.codex/config.toml`

pi has no such limit (`_dist/pi/AGENTS.md` is built the same way and is also 12.6KB currently).

## Update Mechanism — Detailed

### Per-Platform Triggers

| Platform | Method | Trigger |
| --- | --- | --- |
| Cursor | `install.py install` (rsync real-dir, `--delete`) | After repo edits + restart/reload |
| Codex | Local symlink (instant, tracks repo) | After `build` |
| Claude Code | `install.py install` (local-directory marketplace, reinstall = fresh snapshot) | After `build` (when `_dist/` changed); bump optional |
| pi | `install.py install --platform pi` (direct deploy to `~/.pi/agent/`) | After `build` + install |

### Claude Code Version-Gating

The marketplace is registered as a **local directory** (`marketplace_source: "local"` in `third-party.json` → `install.py install` runs `claude plugin marketplace add <REPO_ROOT>`), not a git remote — so `plugin update` reads the working tree directly, no `git fetch`/`push` round-trip.

But the version check is unchanged: Claude compares `plugin.json`'s `version` field against the installed snapshot; same version → it reports "already at latest" and skips the re-snapshot, even when the working tree has changed. Verified: at 1.1.0, content changes without a version bump left the cache at the old snapshot with deleted agents still present. `install.py install`'s reinstall path fixes this (`uninstall`+`install` under the hood, bypasses the version skip).

**Update flow**: edit → `build` (if `_dist/claude/` changed) → `install.py install --platform claude`.

**Bump policy**: bump `plugin.json` + `marketplace.json` together if at all. Claude reads `plugin.json` version only (marketplace.json's version alone is not enough). Bump is diagnostic only — cache dir + `plugin list` reflect the real content either way.

**When a bump is NOT needed**: if `git status _dist/` is clean after `build`, no bump required. Third-party (manual/symlink) skills — mattpocock, understand-anything, anysearch, herdr — live as symlinks in `~/.claude/skills/` (user-level), which Claude scans directly and which **never pass through the plugin cache**. Edits to `install.py`, `third-party.json`, `third-party.schema.json`, or the vendor submodules do NOT require a version bump; on any machine just run `uv run install.py install` (or `install.py manual <name>`) to recreate the symlinks.

### Local vs Remote Marketplace

This repo defaults to local-directory marketplace — no `git push` needed to update Claude's cache, just `build` + `install.py install` (reinstall). The remote-git marketplace path still works for fresh machines: `claude plugin marketplace add https://github.com/EarthChen/ai-assets.git` then `plugin install` (version-gated `plugin update` on refresh). Third-party plugins without `marketplace_source` default to `remote` (git clone, version-gated).

### Cursor Local Plugin — Real Directory, Not Symlink

Cursor local plugin is copied as a **real directory** (not symlink) to `~/.cursor/plugins/local/earthchen-ai-assets`. Cursor's local-plugin scanner skips symlinks in that dir (verified Cursor 2.5.x: symlinked plugin dir is never indexed, skills never load). Codex keeps a symlink — its scanner follows symlinks fine. Restart Cursor or Developer: Reload Window after install.

### Cursor Marketplace Stale-Cache Problem

Cursor resolves a marketplace to a commit SHA on first import and caches it — does NOT re-resolve on reinstall or session start. So marketplace installs get stuck on the first-imported version. For reliable updates use `install.py install` (local real-dir). `cursor` CLI has no `plugin` subcommand, so marketplace install is UI-only (Settings → Customize → add `https://github.com/EarthChen/ai-assets`). Local + marketplace same name → double-load (duplicate skills); pick one, prefer local.

### Cursor "Include third-party Plugins, Skills, and other configs" — Keep OFF

Settings → Rules, Skills, Subagents: when ON, Cursor recursively scans `~/.claude/plugins/cache/*` (every version of this repo's Claude clone, each with full `skills/`), `~/.codex/skills/`, `~/.agents/skills/` with no de-duplication → every skill (e.g. `tdd`) loads ~11×. Known Cursor bug, no ETA. OFF is safe because this repo's own `~/.claude/skills`, `~/.codex/skills`, `~/.agents/skills` are empty — repo-root `skills/` is the sole source.

## Cursor Plugin "Error loading plugin" — Diagnosis

UI提示 "Error loading plugin" **不写进任何文件日志**，console 也只有性能 warn。真实原因只藏在 UI "Copy error details" 按钮的剪贴板里。诊断顺序（踩过 7 轮坑的总结）：

1. **先读剪贴板错误，不要猜配置**：点 UI 卡片旁 `aria-label="Copy error details"` 按钮，`pbpaste` 读。本仓库命中过 `Unable to install plugin without gitPath: Plugin has unresolved or unsafe source path`。
2. **`unresolved or unsafe source path` = marketplace `source` 解析出空 path**。`.claude-plugin/marketplace.json` 的 `source` 必须是字符串相对路径（`"./"` 或 `"./_dist/cursor"`），写成 Claude 的对象格式 `{source,url,ref}` 会让 Cursor 解析出 empty path → 整个 plugin 失败 → skills/agents/rules/MCP 一个都不显示。
3. **`source: "./"` 时 plugin 根 = clone 根 = 仓库根**，前提是仓库根在 fresh clone（不 init submodule）下**零含 `..` 的 symlink**。历史 mattpocock 曾在 `skills/<name>` 建 vendor symlink（含 `..`、fresh clone 断链）触发 unsafe；现已改手动安装，根 `skills/` 只剩 committed 实目录。build 的 `_clean_mattpocock_skill_symlinks` 清理本地残留。
4. **对照成功案例**：`~/.cursor/plugins/cache/cursor-public/superpowers/`（官方）和 `~/.cursor/plugins/marketplaces/github.com/affaan-m/ecc/`（`source: "./"`）。
5. **CDP 抓 console/剪贴板**：Cursor 带 `--remote-debugging-port=9333` 启动，用 Cursor 自带 `ws` 模块连 devtools，`Runtime.evaluate` 点 Copy error details + `pbpaste`。`reload window` 不 re-clone marketplace；要 re-clone 需完全退出 + 删 `~/.cursor/plugins/marketplaces/<host>/<owner>/<repo>/` + 重启。`fresh-clone`（`git clone --depth 1` 到 /tmp）可预先验证仓库根是否干净。

## Third-Party Skills (symlink-installed)

Seven third-party skill sets are **NOT plugin-distributed** — they install as user-level symlinks so their runtime files (`runtime.conf`, `.env`, upstream-pinned content) survive outside the plugin cache (a read-only snapshot overwritten on every version pull). All are declared in `third-party.json` with a top-level `install` object and deployed by `install.py`'s manual-skill path, which **`install.py install` runs automatically** (no separate `install.py manual` needed):

| Skill set | submodule | discovery | links |
| --- | --- | --- | --- |
| **mattpocock-skills** | `vendor/mattpocock-skills` | `generate.from+field` (reads upstream `plugin.json` skills list, 25 skills) | `~/.agents/skills/` |
| **understand-anything** | `vendor/understand-anything` | `generate.scan_dir` (scans `understand-anything-plugin/skills/` for SKILL.md subdirs, 11 skills — upstream `plugin.json` has no skills list) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **anysearch** | `vendor/anysearch-skill` | `links` (explicit list, single skill) | `~/.claude/skills/anysearch` + `~/.agents/skills/anysearch` |
| **herdr** | `vendor/herdr-skill` | `generate.scan_dir` (scans `skills/` — sparse submodule pinned to the single herdr skill) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **playwright-cli** | `vendor/playwright-cli` | `generate.scan_dir` (scans `skills/` — single playwright-cli skill) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **show-me** | `vendor/humanlayer-skills` | `generate.scan_dir` (scans `plugins/show-me/skills/` — humanlayer 5-plugin monorepo, only show-me linked) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **yao-meta-skill** | `vendor/yao-meta-skill` | `links` (explicit list, single skill at repo root) | `~/.claude/skills/yao-meta-skill` + `~/.agents/skills/yao-meta-skill` |

`install.py manual <name>` remains as a single-skill reinstall entry point. All four platforms (Claude, Codex, Cursor, pi) follow these symlinks correctly; no per-platform workaround needed. Adding a third-party skill = adding a `third-party.json` entry with an `install` object (choose `links` for single-skill repos, `generate.from+field` if upstream declares a skill list, `generate.scan_dir` if it doesn't) — no `install.py` code change. See `third-party.schema.json` for the `install`/`installConfig`/`generateConfig` schema.

**context-mode** also has a `third-party.json` entry but is a **provenance record only** — installed per-platform via each platform's native plugin/npm path (Claude: `install.py` auto-runs `claude plugin marketplace add mksglu/context-mode` + `plugin install context-mode@context-mode --scope user`). The entry formalizes the ctx-* tools this repo's docs reference.

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

### yao-meta-skill

[yaojingang/yao-meta-skill](https://github.com/yaojingang/yao-meta-skill) — Skill-OS-style meta skill: create, improve, evaluate, package, and govern reusable agent skills. Single skill at repo root (`SKILL.md` + `references/` + `scripts/` + `reports/`), so distribution uses the `links` pattern (same as anysearch). Replaced the former self-owned `skills/skill-creator` (removed 2026-09-04).

**Upgrade:** `git submodule update --remote vendor/yao-meta-skill` (no upstream release tags — re-pin to a main commit). Symlinks flow automatically.

### mattpocock/skills

Engineering skills from [mattpocock/skills](https://github.com/mattpocock/skills). **Hybrid management** because mattpocock ships only a Claude native plugin (no Codex/Cursor plugin):

- **Claude Code**: provided by native plugin `mattpocock-skills@mattpocock`. NOT in repo-root `skills/`, NOT in `~/.claude/skills/`.
- **Codex / Cursor / pi**: symlinked into `~/.agents/skills/` by `install.py install` (or `install.py manual mattpocock-skills` to reinstall just this set). Reads the upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json` `skills` list (25 entries). Submodule stays at `vendor/mattpocock-skills/`, never touches repo-root `skills/`. Build runs `_clean_mattpocock_skill_symlinks` to remove stale `skills/<name>` links from older builds.

Trade-off vs old build-deep-copy: submodule updates now flow to Codex/Cursor immediately (`git submodule update --remote` → symlinks point at new content, no rebuild needed), but Codex/Cursor users must run `install.py install` once after cloning to create the symlinks (the main install now covers this — no separate `manual` command needed).

**25 skills** (full list with descriptions: `vendor/mattpocock-skills/.claude-plugin/plugin.json`). User-invoked workflow chain: `grill-with-docs` → `to-spec` → `to-tickets` → `implement` → `code-review`. Model-invoked: `tdd`, `diagnosing-bugs`, `research`, `domain-modeling`, `codebase-design`, `prototype`, `grilling`. Productivity: `handoff`, `teach`, `writing-for-agents`, `grill-me`, `to-questionnaire`, `wait-what`. Support: `resolving-merge-conflicts`, `wizard`. Routers: `ask-matt`, `wayfinder`, `triage`, `improve-codebase-architecture`, `setup-matt-pocock-skills`.

```bash
uv run install.py manual mattpocock-skills              # install all 25
git submodule update --remote vendor/mattpocock-skills  # update upstream (symlinks auto-flow)
# then re-pin to a release tag: git add vendor/mattpocock-skills
```

## Common Workflows

**Adding a new skill**: drop `skills/<name>/SKILL.md` + optional `references/`. Run `uv run install.py build`. No `_dist/` change unless the skill listing affects a manifest. Commit.

**Adding a new agent**: drop `agents/<name>.md`. Run `uv run install.py build` — `_sync_claude_manifest_agents` updates `.claude-plugin/plugin.json`. Commit both files.

**Adding a new rule**: see `README.md` Rules 系统详解 (or AGENTS.md if that's where rules deployment strategy lives).

**Bumping versions**: `uv run install.py version --bump patch` (major/minor/patch). Updates `.claude-plugin/{plugin,marketplace}.json`. Optional — see Claude Code Version-Gating above.

**Adding a vendor submodule**: drop into `vendor/<name>/`, add to `.gitmodules`. For skill distribution, add a `third-party.json` entry with an `install` object.

## Debugging a Failed Build

```bash
# 1. Verify Python env
uv run python --version  # needs >=3.10

# 2. Dry-run build to surface errors without writing
uv run install.py build --dry-run

# 3. Check _dist/ contents
ls _dist/claude/rules/ _dist/cursor/rules/ _dist/codex/

# 4. Validate Claude manifest (catches `agents: Invalid input` errors)
uv run python -c "import json; json.load(open('.claude-plugin/plugin.json'))"

# 5. Check Codex AGENTS.md size budget
wc -c _dist/codex/AGENTS.md  # must be < 32KB
```

If `install.py build` fails with a stack trace, the issue is usually:

- A malformed YAML frontmatter in a rule (unclosed `---`)
- A skill `references/<file>.md` that doesn't exist (link rot)
- A `.mcp.json` with invalid `_platforms` syntax
