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

1. **Source (single truth)** — `rules/`, `skills/`, `agents/`, `mcp.json`, `global-instructions.md`, `install.py` + `installer/`, `.claude-plugin/`, `.cursor-plugin/`, `third-party.json`
2. **`_dist/` (per-platform outputs, committed)** — `cursor/`, `claude/`, `codex/`, `pi/`

`install.py build` regenerates `_dist/` from source. Skills and agents are **not** copied into `_dist/` — Claude scans the repo root `skills/`/`agents/` through its plugin, Cursor reads `agents/` from its plugin copy, and pi, Cursor and Codex get self-owned skills through `~/.agents/skills` symlinks. `build` does not read `skills/` or `agents/` at all. `_dist/` holds only what genuinely differs per platform:

- `mcp.json` (`_platforms` filter) — written even when the filter yields zero servers: repo-root `.mcp.json` symlinks to `_dist/claude/mcp.json`, so skipping the write dangles it (that was the state until 2026-10-08). Claude accepts an empty `{"mcpServers": {}}` plugin file.
- `rules/` (`.mdc` vs `.md` + frontmatter transform)
- `global-instructions.md` deploy (becomes `CLAUDE.md` / `AGENTS.md`)

Known gap: `_dist/codex/mcp.json` is generated but nothing reads it. Codex loads no repo plugin, so a server tagged `_platforms: ["codex"]` never reaches Codex. The file is empty today.

Why commit `_dist/`? Marketplace installs (Cursor marketplace, Claude remote marketplace) clone the repo and read `_dist/` as committed; they never run `build`. Local deploys still need `install.py install` after `build`: Cursor reads a real-dir copy, Codex reads `~/.codex/AGENTS.md` (a copy; only its skills track the repo through the plugin symlink), Claude Code reads a reinstalled snapshot, and pi reads `~/.pi/agent/AGENTS.md`. `uv run pytest` fails when the committed `_dist/` differs from a fresh build.

### Claude Plugin Manifest (`.claude-plugin/plugin.json`) — No `agents`, No `skills`

Claude Code auto-scans the plugin-root `agents/` and `skills/` dirs. Declaring either key does not add to that scan — for `agents` it replaces it with a resolver that loads nothing:

- **`agents` must stay absent.** Probe-verified 2026-10-08 on Claude Code 2.1.285: two plugins sharing an identical `agents/probe-agent.md`, the one declaring `"agents": ["./agents/probe-agent.md"]` reported `Agents (0)` in `claude plugin details`, the one without the key reported `Agents (1)`. `claude plugin validate` passes either way, so the failure is silent — this repo shipped 12 declared agents that Claude never loaded. A directory value (`"./agents/"`, which is what `.cursor-plugin/plugin.json` uses) is worse: it fails validation with `agents: Invalid input`. Anthropic's own plugins (`feature-dev`, `plugin-dev`, `pr-review-toolkit`, `code-modernization`, `agent-sdk-dev`, `hookify`, `code-simplifier`, `claude-security`) all ship an `agents/` dir with no `agents` key.
- **`skills`** is deliberately omitted. Per schema it *adds to* the default `skills/` scan, so setting it would duplicate. Claude scans the plugin-root `skills/` directly, which holds only the self-owned skills (mattpocock/anysearch are manual-installed elsewhere).

`install.py build` runs `_ensure_claude_manifest_autoscan()`, which strips an `agents` key if one is ever committed again.

After adding or removing an agent, commit `agents/<name>.md` and nothing else — there is no manifest to sync. Verify what Claude actually loaded with `claude plugin details earthchen-ai-assets@earthchen-ai-assets`: the component inventory must list every agent.

## Build Transforms (rules frontmatter → per-platform)

| Source field | → Cursor (.mdc) | → Claude Code (.md) | → Codex (AGENTS.md) |
| --- | --- | --- | --- |
| `paths: [...]` | `globs: [...]` (JSON array) | `paths: csv` (CSV string + `alwaysApply: false`) | stripped (plain text) |
| `globs: [...]` | kept as JSON array | → `paths: csv` (converted + `alwaysApply: false`) | stripped |
| `platforms: [...]` | removed | removed | used for filtering then stripped |
| `description` | kept | kept | stripped |
| `alwaysApply` | kept | kept | stripped |

## Codex AGENTS.md 32KB Limit

Codex reads `~/.codex/AGENTS.md` under a 32KB ceiling (`project_doc_max_bytes`). `install.py build` composes that file from **`global-instructions.md` + every `rules/common/*.md` that passes the codex platform filter** (frontmatter stripped) → `_dist/codex/AGENTS.md` → deployed on install. Current size: 11.5KB (well under).

Repo-root `AGENTS.md` is **not** part of the embed — it is maintainer documentation only, so its length never touches the Codex budget. Moving text between `global-instructions.md` and `rules/common/` is likewise a no-op for size: both are embedded.

If you approach the limit, in order of preference:

1. Move detailed踩坑 knowledge out to CONTRIBUTING.md (this file) — not embedded
2. Demote an always-on `rules/common/*.md` into a skill reference, so it loads on demand instead of every turn — the same move the java/python rules just made
3. As last resort: raise `project_doc_max_bytes` in `~/.codex/config.toml`

pi has no such limit (`_dist/pi/AGENTS.md` is built the same way and is also 11.5KB currently).

## Update Mechanism — Detailed

### Per-Platform Triggers

| Platform | Method | Trigger |
| --- | --- | --- |
| Cursor | `install.py install` (rsync real-dir, `--delete`) | After repo edits: `install` (+ `build` first if rules/MCP changed) + restart/reload |
| Codex | `~/.agents/skills` symlinks (no repo plugin; `install` disables a previously registered one); `~/.codex/AGENTS.md` is a copy | Skills: edits instant, new/renamed ones need `install`. AGENTS.md: `build` + `install` |
| Claude Code | `install.py install` (local-directory marketplace, reinstall = fresh snapshot) | After repo edits: `install` (+ `build` first if `_dist/` inputs changed); bump optional |
| pi | `install.py install --platform pi` (AGENTS.md copy + skill/agent symlinks under `~/.pi/agent/`) | AGENTS.md: `build` + `install`; skill/agent edits instant, new/renamed ones need `install` |

### Claude Code Version-Gating

The marketplace is registered as a **local directory** (`marketplace_source: "local"` in `third-party.json` → `install.py install` runs `claude plugin marketplace add <REPO_ROOT>`), not a git remote — so `plugin update` reads the working tree directly, no `git fetch`/`push` round-trip.

But the version check is unchanged: Claude compares `plugin.json`'s `version` field against the installed snapshot; same version → it reports "already at latest" and skips the re-snapshot, even when the working tree has changed. Verified: at 1.1.0, content changes without a version bump left the cache at the old snapshot with deleted agents still present. `install.py install`'s reinstall path fixes this (`uninstall`+`install` under the hood, bypasses the version skip).

**Update flow**: edit → `build` (if `_dist/claude/` changed) → `install.py install --platform claude`.

**Snapshot accumulation**: every reinstall writes a fresh `~/.claude/plugins/cache/earthchen-ai-assets/earthchen-ai-assets/<version>/`, and Claude's own sweep is unreliable — a stale `.in_use` lock pinned a 2026-07 snapshot for months. The local marketplace source is the repo root, so each snapshot of this repo carries `vendor/` as well (26M measured 2026-10-14; earlier snapshots that also carried a local `node_modules/` measured ~136M). `install_claude` therefore prunes this plugin's non-current snapshots right after the reinstall (`_prune_claude_plugin_cache`); it deletes nothing when the current version's directory is missing, so a failed reinstall cannot wipe the only working copy. Other plugins' caches are left alone.

**Bump policy**: bump `plugin.json` + `marketplace.json` together if at all. Claude reads `plugin.json` version only (marketplace.json's version alone is not enough). Bump is diagnostic only — cache dir + `plugin list` reflect the real content either way.

**When a bump is NOT needed**: if `git status _dist/` is clean after `build`, no bump required. Third-party (manual/symlink) skills — the nine sets listed under Third-Party Skills below — live as user-level symlinks in `~/.claude/skills/` and/or `~/.agents/skills/`, which **never pass through the plugin cache** (on Claude, mattpocock comes from its own native plugin instead). Edits to `install.py`, `third-party.json`, `third-party.schema.json`, or the vendor submodules do NOT require a version bump; on any machine just run `uv run install.py install` (or `install.py manual <name>`) to recreate the symlinks.

### Local vs Remote Marketplace

This repo defaults to local-directory marketplace — no `git push` needed to update Claude's cache, just `build` + `install.py install` (reinstall). The remote-git marketplace path still works for fresh machines: `claude plugin marketplace add https://github.com/EarthChen/ai-assets.git` then `plugin install` (version-gated `plugin update` on refresh). Third-party plugins without `marketplace_source` default to `remote` (git clone, version-gated).

### Cursor Local Plugin — Real Directory, Not Symlink

Cursor local plugin is copied as a **real directory** (not symlink) to `~/.cursor/plugins/local/earthchen-ai-assets`. Cursor's local-plugin scanner skips symlinks in that dir (verified Cursor 2.5.x: symlinked plugin dir is never indexed). The copy omits the root `skills/` and the manifest declares no `skills` field: Cursor auto-discovers a plugin's `skills/` and does not de-duplicate by name, and it already reads self-owned skills from `~/.agents/skills`. Restart Cursor or Developer: Reload Window after install.

### Cursor Marketplace Stale-Cache Problem

Cursor resolves a marketplace to a commit SHA on first import and caches it — does NOT re-resolve on reinstall or session start. So marketplace installs get stuck on the first-imported version. For reliable updates use `install.py install` (local real-dir). `cursor` CLI has no `plugin` subcommand, so marketplace install is UI-only (Settings → Customize → add `https://github.com/EarthChen/ai-assets`). Local + marketplace same name → double-load (duplicate skills); pick one, prefer local.

### Cursor "Include third-party Plugins, Skills, and other configs" — Keep OFF

Settings → Rules, Skills, Subagents: when ON, Cursor recursively scans `~/.claude/plugins/cache/*` (every version of this repo's Claude clone, each with full `skills/`), `~/.codex/skills/`, `~/.agents/skills/` with no de-duplication → every skill (e.g. `tdd`) loads ~11×. Known Cursor bug, no ETA. OFF avoids the plugin-cache and `~/.claude/skills` / `~/.codex/skills` scans. Cursor's docs (Skill directories, checked 2026-10-14) list `~/.agents/skills/` as a default user-level dir, so it loads regardless of this toggle. `install` links self-owned skills there, which is why the Cursor plugin copy ships no `skills/`. A Cursor **marketplace** install of this repo would ship `skills/` again and duplicate them, so use the local copy only.

## pi Deploy (script-only)

[pi](https://github.com/badlogic/pi-mono) has no plugin system compatible with this repo, so `install.py install --platform pi` deploys directly to `~/.pi/agent/`:

- **AGENTS.md**: `_dist/pi/AGENTS.md` (global-instructions + common rules, same embed as Codex; pi loads it from `~/.pi/agent/` at startup — no 32KB limit) → `~/.pi/agent/AGENTS.md`, **full overwrite** (repo is the single source of truth; my-pi-agent's own project docs live in that repo's CLAUDE.md)
- **Skills**: self-owned skills (`skills/*`) symlinked into `~/.agents/skills/` by the shared install step on every `install` run — the Agent Skills standard dir, read by pi, Cursor and Codex; same dir as the third-party links from `install.py manual` (mattpocock, anysearch, ...). Not registered via `settings.json`. `install_pi` removes self-owned links from `~/.pi/agent/skills/` (left by older installs) so pi loads each skill once; vendor links and real directories stay
- **pi-only skills**: `pi/skills/*` symlinked into `~/.pi/agent/skills/` — pi reads that dir and no other harness does, and it sits outside the plugin-root `skills/`, so these skills load exclusively on pi. Currently: none (`herdr-orchestration` moved to root `skills/` — it went multi-platform: orchestrator AND workers can run on pi, Claude Code, or Codex, mixed pools allowed)
- **Agents**: `agents/*.md` symlinked into `~/.pi/agent/agents/` — pi-subagents' `discoverAgents()` scans that user dir (alongside its builtins scout/reviewer/worker/...) and loads `*.md` with YAML frontmatter. Repo agent frontmatter only sets `name` + `description`; `model` and `tools` are intentionally omitted so pi-subagents inherits the parent session's model and grants the default tool set. Verify with `/subagents-doctor` + `subagent({ action: "list" })` after install.
- **pi-only agents**: `pi/agents/*.md` symlinked into the same `~/.pi/agent/agents/` dir — they sit outside the plugin-root `agents/` that Claude auto-scans and outside the `./agents/` path Cursor's manifest declares, so these load exclusively on pi. Currently: `Explore.md`
- **NOT deployed**: MCP (pi covers playwright etc. via its own extensions — no `mcp.json` sync), separate rules files (embedded in AGENTS.md; language conventions via `skills/<lang>-development` on demand)

## Cursor Plugin "Error loading plugin" — Diagnosis

UI提示 "Error loading plugin" **不写进任何文件日志**，console 也只有性能 warn。真实原因只藏在 UI "Copy error details" 按钮的剪贴板里。诊断顺序（踩过 7 轮坑的总结）：

1. **先读剪贴板错误，不要猜配置**：点 UI 卡片旁 `aria-label="Copy error details"` 按钮，`pbpaste` 读。本仓库命中过 `Unable to install plugin without gitPath: Plugin has unresolved or unsafe source path`。
2. **`unresolved or unsafe source path` = marketplace `source` 解析出空 path**。`.claude-plugin/marketplace.json` 的 `source` 必须是字符串相对路径（`"./"` 或 `"./_dist/cursor"`），写成 Claude 的对象格式 `{source,url,ref}` 会让 Cursor 解析出 empty path → 整个 plugin 失败 → skills/agents/rules/MCP 一个都不显示。
3. **`source: "./"` 时 plugin 根 = clone 根 = 仓库根**，前提是仓库根在 fresh clone（不 init submodule）下**零含 `..` 的 symlink**。历史 mattpocock 曾在 `skills/<name>` 建 vendor symlink（含 `..`、fresh clone 断链）触发 unsafe；现已改手动安装，根 `skills/` 只剩 committed 实目录。build 的 `_clean_mattpocock_skill_symlinks` 清理本地残留。
4. **对照成功案例**：`~/.cursor/plugins/cache/cursor-public/superpowers/`（官方）和 `~/.cursor/plugins/marketplaces/github.com/affaan-m/ecc/`（`source: "./"`）。
5. **CDP 抓 console/剪贴板**：Cursor 带 `--remote-debugging-port=9333` 启动，用 Cursor 自带 `ws` 模块连 devtools，`Runtime.evaluate` 点 Copy error details + `pbpaste`。`reload window` 不 re-clone marketplace；要 re-clone 需完全退出 + 删 `~/.cursor/plugins/marketplaces/<host>/<owner>/<repo>/` + 重启。`fresh-clone`（`git clone --depth 1` 到 /tmp）可预先验证仓库根是否干净。

## Third-Party Skills (symlink-installed)

Nine third-party skill sets are **NOT plugin-distributed** — they install as user-level symlinks so their runtime files (`runtime.conf`, `.env`, upstream-pinned content) survive outside the plugin cache (a read-only snapshot overwritten on every version pull). All are declared in `third-party.json` with a top-level `install` object and deployed by `install.py`'s manual-skill path, which **`install.py install` runs automatically** (no separate `install.py manual` needed):

| Skill set | submodule | discovery | links |
| --- | --- | --- | --- |
| **mattpocock-skills** | `vendor/mattpocock-skills` | `generate.from+field` (reads upstream `plugin.json` skills list, 27 skills) | `~/.agents/skills/` |
| **understand-anything** | `vendor/understand-anything` | `generate.scan_dir` (scans `understand-anything-plugin/skills/` for SKILL.md subdirs, 11 skills — upstream `plugin.json` has no skills list) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **anysearch** | `vendor/anysearch-skill` | `links` (explicit list, single skill) | `~/.claude/skills/anysearch` + `~/.agents/skills/anysearch` |
| **herdr** | `vendor/herdr-skill` | `generate.scan_dir` (scans `skills/` — sparse submodule pinned to the single herdr skill) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **playwright-cli** | `vendor/playwright-cli` | `generate.scan_dir` (scans `skills/` — single playwright-cli skill) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **ego-browser** | `vendor/ego-lite` | `generate.scan_dir` (scans `skills/` — sparse submodule pinned to the single ego-browser skill) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **show-me** | `vendor/humanlayer-skills` | `generate.scan_dir` (scans `plugins/show-me/skills/` — humanlayer 6-plugin monorepo, show-me + visual-pr linked) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **visual-pr** | `vendor/humanlayer-skills` | `generate.scan_dir` (scans `plugins/visual-pr/skills/` — same submodule as show-me) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **yao-meta-skill** | `vendor/yao-meta-skill` | `links` (explicit list, single skill at repo root) | `~/.claude/skills/yao-meta-skill` + `~/.agents/skills/yao-meta-skill` |

`install.py manual <name>` remains as a single-skill reinstall entry point. All four platforms (Claude, Codex, Cursor, pi) follow these symlinks correctly; no per-platform workaround needed. Adding a third-party skill = adding a `third-party.json` entry with an `install` object (choose `links` for single-skill repos, `generate.from+field` if upstream declares a skill list, `generate.scan_dir` if it doesn't) — no `install.py` code change. See `third-party.schema.json` for the `install`/`installConfig`/`generateConfig` schema.

**Stale-link caveat**: `install_manual_skills` only creates links — it never prunes. When upstream deletes or renames a skill, the old link survives as a dangling symlink, so after any vendor upgrade check `find ~/.agents/skills ~/.claude/skills -maxdepth 1 -type l ! -exec test -e {} \; -print` and delete what it lists. Hit in practice: a 2026-09 upstream skill deletion left one behind.

**context-mode** also has a `third-party.json` entry but is a **provenance record only** — installed per-platform via each platform's native plugin/npm path (Claude: `install.py` auto-runs `claude plugin marketplace add mksglu/context-mode` + `plugin install context-mode@context-mode --scope user`). The entry formalizes the ctx-* tools this repo's docs reference.

### anysearch-skill

[anysearch-ai/anysearch-skill](https://github.com/anysearch-ai/anysearch-skill) is a CLI skill (calls `api.anysearch.com`, NOT an MCP server) replacing the former `exa` MCP server. Pinned at `vendor/anysearch-skill/` (submodule).

**Why not plugin-distributed?** The skill needs `runtime.conf` (agent-written at first use) and optional `.env` (`ANYSEARCH_API_KEY`) to persist across sessions. But plugin cache (`~/.claude/plugins/cache/.../`) is a **read-only snapshot overwritten on every version pull** — files the agent writes there are lost next session. So anysearch installs as user-level symlinks outside the plugin cache, where persistent files survive.

**Upgrade:** `git submodule update --remote vendor/anysearch-skill` (re-pin to a release tag). Symlinks need no update — content flows through automatically.

### understand-anything

[EarthChen/Understand-Anything](https://github.com/EarthChen/Understand-Anything) — AI-powered codebase understanding: analyze, visualize, and explain any project via an interactive knowledge graph. Submodule at `vendor/understand-anything`; 11 skills under `understand-anything-plugin/skills/<name>/SKILL.md` plus a `shared/` lib dir (not a skill, skipped by `scan_dir`). Upstream `plugin.json` carries no `skills` list, so discovery uses `generate.scan_dir`.

Not plugin-distributed for the same reason as anysearch: runtime files (`system.json`, generated graphs under `.understand-anything/`) must survive across sessions outside the read-only plugin cache.

**Upgrade:** `git submodule update --remote vendor/understand-anything` (re-pin to a tag if upstream tags one). Symlinks need no update — content flows through automatically.

### ego-browser

[citrolabs/ego-lite](https://github.com/citrolabs/ego-lite) browser skill, pinned as a **sparse submodule** at `vendor/ego-lite` (only `skills/ego-browser` checked out; the rest of the repo is ~8MB of docs and packaging). The skill is a bootstrap stub: its `SKILL.md` tells the agent to run `ego-browser skill`, which prints the guide that matches the installed ego lite app. Skill content therefore does not drift from the binary.

- **Runtime dependency**: the ego lite desktop app (macOS only; GUI onboarding puts `ego-browser` on PATH). Without it the skill is inert.
- **Link collision**: the ego lite app symlinks its own copy to `~/.agents/skills/ego-browser`. `install.py install` re-points that link at the submodule (`create_symlink` replaces existing symlinks). Both copies defer to the binary's guide, so the swap is harmless.
- **Not a Playwright replacement**: custom JS API (no `locator()`, `expect()`, `route()`), needs a GUI session, so no headless or CI use. `e2e-runner` and `e2e-testing` stay on `playwright-cli` / Playwright Test. Use ego-browser when the task needs the user's logged-in browser state.
- **Do not automate `skills/ego-browser/scripts/install.sh`**: it downloads a DMG and may call `sudo`.

**Upgrade:** `git submodule update --remote vendor/ego-lite` (re-pin to a release tag; currently `v2.1.0`). Symlinks flow automatically.

### herdr-skill

The [herdr](https://github.com/badlogic/herdr) terminal-multiplexer control skill, pinned as a **sparse submodule** at `vendor/herdr-skill` (tracks upstream, checks out only the single skill). Same symlink distribution as the other sets; gives Claude/Codex/Cursor/pi the `herdr` CLI etiquette without vendoring the whole upstream repo.

**Upgrade:** `git submodule update --remote vendor/herdr-skill`. Symlinks flow automatically.

### yao-meta-skill

[yaojingang/yao-meta-skill](https://github.com/yaojingang/yao-meta-skill) — Skill-OS-style meta skill: create, improve, evaluate, package, and govern reusable agent skills. Single skill at repo root (`SKILL.md` + `references/` + `scripts/` + `reports/`), so distribution uses the `links` pattern (same as anysearch). Replaced the former self-owned `skills/skill-creator` (removed 2026-09-04).

**Upgrade:** `git submodule update --remote vendor/yao-meta-skill` (no upstream release tags — re-pin to a main commit). Symlinks flow automatically.

### mattpocock/skills

Engineering skills from [mattpocock/skills](https://github.com/mattpocock/skills). **Hybrid management** because mattpocock ships only a Claude native plugin (no Codex/Cursor plugin):

- **Claude Code**: provided by native plugin `mattpocock-skills@mattpocock`. NOT in repo-root `skills/`, NOT in `~/.claude/skills/`.
- **Codex / Cursor / pi**: symlinked into `~/.agents/skills/` by `install.py install` (or `install.py manual mattpocock-skills` to reinstall just this set). Reads the upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json` `skills` list (27 entries). Submodule stays at `vendor/mattpocock-skills/`, never touches repo-root `skills/`. Build runs `_clean_mattpocock_skill_symlinks` to remove stale `skills/<name>` links from older builds.

Trade-off vs old build-deep-copy: submodule updates now flow to Codex/Cursor immediately (`git submodule update --remote` → symlinks point at new content, no rebuild needed), but Codex/Cursor users must run `install.py install` once after cloning to create the symlinks (the main install now covers this — no separate `manual` command needed).

**27 skills** (full list with descriptions: `vendor/mattpocock-skills/.claude-plugin/plugin.json`). User-invoked workflow chain: `grill-with-docs` → `to-spec` → `to-tickets` → `implement` / `implement-spec` → `pr` → `code-review` → `retro`. Model-invoked: `tdd`, `diagnosing-bugs`, `research`, `domain-modeling`, `codebase-design`, `prototype`, `grilling`. Productivity: `handoff`, `teach`, `writing-for-agents`, `grill-me`, `to-questionnaire`, `wait-what`. Support: `wizard`. Routers: `ask-matt`, `wayfinder`, `triage`, `improve-codebase-architecture`, `setup-matt-pocock-skills`.

Upstream v1.3.0 deleted its merge-conflict skill with no replacement (it keeps an archived doc page only), so `skills/ship-to-test/SKILL.md` inlines the conflict-resolution mechanics instead of delegating them to a skill.

```bash
uv run install.py manual mattpocock-skills              # install all 27
git submodule update --remote vendor/mattpocock-skills  # update upstream (symlinks auto-flow)
# then re-pin to a release tag: git add vendor/mattpocock-skills
```

## Common Workflows

**Adding a new skill**: drop `skills/<name>/SKILL.md` + optional `references/`. No `build` needed (`build` does not read `skills/`). Run `uv run install.py install` so Claude's snapshot and the `~/.agents/skills` symlink (pi, Cursor, Codex) pick it up. Commit.

**Adding a new agent**: drop `agents/<name>.md` and commit it. Claude auto-scans the dir (the manifest must NOT list agents — see Claude Plugin Manifest above); pi gets a symlink on `install.py install --platform pi`; Cursor reads `"agents": "./agents/"` from its own manifest. Verify Claude's count with `claude plugin details earthchen-ai-assets@earthchen-ai-assets`.

**Adding a new rule**: see `README.md` Rules 系统详解 (or AGENTS.md if that's where rules deployment strategy lives).

**Bumping versions**: `uv run install.py version --bump patch` (major/minor/patch). Updates `.claude-plugin/{plugin,marketplace}.json` and `.cursor-plugin/plugin.json`. Optional — see Claude Code Version-Gating above.

**Running tests**: `uv run pytest`. Tests use a scratch HOME and never touch `~/`. The golden test builds a copy of the repo and fails when the committed `_dist/` is stale — run `uv run install.py build` and commit `_dist/`. Installer code lives in `installer/` (one module per phase/platform); `install.py` is only the entrypoint.

**Adding a vendor submodule**: drop into `vendor/<name>/`, add to `.gitmodules`. For skill distribution, add a `third-party.json` entry with an `install` object.

## Debugging a Failed Build

```bash
# 1. Verify Python env
uv run python --version  # needs >=3.10

# 2. Dry-run build to surface errors without writing
uv run install.py build --dry-run

# 3. Check _dist/ contents
ls _dist/claude/rules/ _dist/cursor/rules/ _dist/codex/

# 4. Validate the Claude manifest, then check what Claude actually loaded
uv run python -c "import json; json.load(open('.claude-plugin/plugin.json'))"
claude plugin validate .
claude plugin details earthchen-ai-assets@earthchen-ai-assets  # skills/agents/MCP counts

# 5. Check Codex AGENTS.md size budget
wc -c _dist/codex/AGENTS.md  # must be < 32KB
```

If `install.py build` fails with a stack trace, the issue is usually:

- A malformed YAML frontmatter in a rule (unclosed `---`)
- A `mcp.json` (source, repo root) with invalid JSON or `_platforms` syntax
