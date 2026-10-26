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

1. **Source (single truth)** — `rules/`, `skills/`, `agents/`, `mcp.json`, `global-instructions.md`, `install.py` + `installer/`, `.cursor-plugin/`, `third-party.json`
2. **`_dist/` (per-platform outputs, committed)** — `cursor/`, `codex/`, `pi/` (Claude has none: it links the sources)

`install.py build` regenerates `_dist/` from source. Skills and agents are **not** copied into `_dist/` — Claude scans the repo root `skills/`/`agents/` through its plugin, Cursor reads `agents/` from its plugin copy, and pi, Cursor and Codex get self-owned skills through `~/.agents/skills` symlinks. `build` does not read `skills/` or `agents/` at all. `_dist/` holds only what genuinely differs per platform:

- `mcp.json` (`_platforms` filter) — written even when the filter yields zero servers, so the committed file set stays stable. Only Cursor consumes it.
- `rules/` (`.mdc` vs `.md` + frontmatter transform)
- `global-instructions.md` deploy (becomes `CLAUDE.md` / `AGENTS.md`)

Known gap: `_dist/codex/mcp.json` is generated but nothing reads it. Codex loads no repo plugin, so a server tagged `_platforms: ["codex"]` never reaches Codex. The file is empty today.

Why commit `_dist/`? Marketplace installs (Cursor marketplace, Claude remote marketplace) clone the repo and read `_dist/` as committed; they never run `build`. Local deploys still need `install.py install` after `build`: Cursor reads a real-dir copy, Codex reads `~/.codex/AGENTS.md` (a copy; only its skills track the repo through the plugin symlink), Claude Code reads symlinks to the sources (skills and agents instantly; `CLAUDE.md` and rules at session start, with no `build`), and pi reads `~/.pi/agent/AGENTS.md`. `uv run pytest` fails when the committed `_dist/` differs from a fresh build.

### Plugin Manifests: Only Cursor Loads a Repo Plugin

Cursor owns the one marketplace manifest, `.cursor-plugin/marketplace.json` + `.cursor-plugin/plugin.json`. Its source is `./` (repo root) and its content is agents, rules and MCP.

Claude has no repo plugin. It links skills, agents, `CLAUDE.md` and rules into `~/.claude` (see Claude Symlink Deploy below). A Claude plugin rooted at the repo root would load every skill and agent a second time, so `tests/test_plugin_manifests.py` fails when `.claude-plugin/` exists.

## Build Transforms (rules frontmatter → per-platform)

Claude Code gets no build output for rules: it links `rules/common` as is, so a `rules/common` file must already be valid Claude frontmatter (`description`, `alwaysApply: true`; user-level `paths` is ignored). `build` fails when a `rules/common` file's `platforms` excludes claude; platform-only rules live in `rules/<platform>/`.

| Source field | → Cursor (.mdc) | → Codex (AGENTS.md) |
| --- | --- | --- |
| `paths: [...]` | `globs: [...]` (JSON array) | stripped (plain text) |
| `globs: [...]` | kept as JSON array | stripped |
| `platforms: [...]` | removed | used for filtering then stripped |
| `description` | kept | stripped |
| `alwaysApply` | kept | stripped |

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
| Claude Code | `install.py install --platform claude`: symlinks in `~/.claude/{skills,agents}`, `~/.claude/CLAUDE.md`, `~/.claude/rules/common` | Skills, agents: edits instant, new/renamed ones need `install`. `CLAUDE.md`, rules: edit, then a new session (no `build`, no `install`) |
| pi | `install.py install --platform pi` (AGENTS.md copy + skill/agent symlinks under `~/.pi/agent/`) | AGENTS.md: `build` + `install`; skill/agent edits instant, new/renamed ones need `install` |

### Claude Symlink Deploy

`install_claude` (`installer/deploy_claude.py`) links the repo into `~/.claude`; nothing is copied or snapshotted:

| Asset | Link | Reload |
| --- | --- | --- |
| Skills | `~/.claude/skills/<name>` → `skills/<name>` | In-session (documented) |
| Agents | `~/.claude/agents/<name>.md` → `agents/<name>.md` | Within seconds; the first agent file in a new `agents/` dir needs a restart |
| `CLAUDE.md` | `~/.claude/CLAUDE.md` → `global-instructions.md` | New session; no `build` |
| Rules | `~/.claude/rules/common` → `rules/common` | New session; no `build`, new rule files need no `install` either (directory link) |
| Hooks | none | Not deployed. Add hooks by hand in `~/.claude/settings.json` |
| MCP | none | Manual: `claude mcp add-json --scope user <name> '<json>'` |

- **Why no MCP deploy**: user-scope servers live in `~/.claude.json`, which also holds oauth state, caches and per-project history and which Claude rewrites at runtime. A symlink or copy would clobber it. The one repo entry is tagged `cursor`, so Claude needs none today.
- **Names**: skills and agents are bare (`code-audit`, not `earthchen-ai-assets:code-audit`). Same-name agents resolve by priority (user over plugin); same-name skills both load.
- **Real files are safe**: a different `CLAUDE.md` is kept as `CLAUDE.md.pre-link.bak`; a real agent file with a repo agent's name is skipped with a warning; the old copied `rules/common` dir is replaced.
- **Unverified in the docs**: symlinks for `~/.claude/CLAUDE.md`, `~/.claude/rules/` and `~/.claude/agents/` (skills are documented). After the first install, start a session and confirm the rules and agents load.
- Third-party (manual/symlink) skills use the same `~/.claude/skills/`; the nine sets listed under Third-Party Skills below are unaffected.

### Local vs Remote Marketplace

Third-party Claude plugins in `third-party.json` use `marketplace_source`: `remote` (default; git clone, version-gated `plugin update`) or `local` (directory marketplace, reinstall on every `install`). This repo's own plugin is no longer registered; Claude gets it through symlinks.

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
2. **`unresolved or unsafe source path` = marketplace `source` 解析出空 path**。`.cursor-plugin/marketplace.json` 的 `source` 必须是字符串相对路径（`"./"` 或 `"./_dist/cursor"`），写成 Claude 的对象格式 `{source,url,ref}` 会让 Cursor 解析出 empty path → 整个 plugin 失败 → skills/agents/rules/MCP 一个都不显示。
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
| **show-me** | `vendor/humanlayer-skills` | `generate.scan_dir` (scans `plugins/show-me/skills/` — humanlayer 6-plugin monorepo, show-me + visual-pr linked) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **visual-pr** | `vendor/humanlayer-skills` | `generate.scan_dir` (scans `plugins/visual-pr/skills/` — same submodule as show-me) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |
| **yao-meta-skill** | `vendor/yao-meta-skill` | `links` (explicit list, single skill at repo root) | `~/.claude/skills/yao-meta-skill` + `~/.agents/skills/yao-meta-skill` |
| **momo-tools** | `vendor/momo-tools` | `generate.scan_dir` (scans `skills/` — single momo-tools skill; private upstream) | `~/.agents/skills/` + `~/.claude/skills/` (via `extra_links`) |

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

### herdr-skill

The [herdr](https://github.com/badlogic/herdr) terminal-multiplexer control skill, pinned as a **sparse submodule** at `vendor/herdr-skill` (tracks upstream, checks out only the single skill). Same symlink distribution as the other sets; gives Claude/Codex/Cursor/pi the `herdr` CLI etiquette without vendoring the whole upstream repo.

**Upgrade:** `git submodule update --remote vendor/herdr-skill`. Symlinks flow automatically.

### yao-meta-skill

[yaojingang/yao-meta-skill](https://github.com/yaojingang/yao-meta-skill) — Skill-OS-style meta skill: create, improve, evaluate, package, and govern reusable agent skills. Single skill at repo root (`SKILL.md` + `references/` + `scripts/` + `reports/`), so distribution uses the `links` pattern (same as anysearch). Replaced the former self-owned `skills/skill-creator` (removed 2026-09-04).

**Upgrade:** `git submodule update --remote vendor/yao-meta-skill` (no upstream release tags — re-pin to a main commit). Symlinks flow automatically.

### momo-tools

[EarthChen/momo-tools](https://github.com/EarthChen/momo-tools) — CLIs and one skill for wemomo.com internal systems (`hubble`, `mse`, `kibana`, `store`). Full (not sparse) submodule at `vendor/momo-tools`: the repo is small, and the checkout doubles as the CLI install source.

- **Private upstream**: this repo is public, so the `.gitmodules` URL and the pinned SHA are visible; the skill content is not. A clone without access to `EarthChen/momo-tools` fails to init the submodule; `install_manual_skills` logs the error and skips the entry, and the other skills still install.
- **Runtime dependency**: the skill calls the CLIs on PATH. Install them with `uv tool install --force vendor/momo-tools` (or from any local clone). Without them the skill tells the agent to ask the user to install.

**Upgrade:** `git submodule update --remote vendor/momo-tools` (no upstream release tags — re-pin to a main commit). Symlinks flow automatically; rerun `uv tool install --force` to update the CLIs.

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

**Adding a new skill**: drop `skills/<name>/SKILL.md` + optional `references/`. No `build` needed (`build` does not read `skills/`). Run `uv run install.py install` so the `~/.claude/skills` and `~/.agents/skills` symlinks (Claude; pi, Cursor, Codex) pick it up. Commit.

**Adding a new agent**: drop `agents/<name>.md` and commit it. Claude gets a symlink in `~/.claude/agents/` on `install.py install --platform claude`; pi gets one on `--platform pi`; Cursor reads `"agents": "./agents/"` from its own manifest.

**Adding a new rule**: see `README.md` Rules 系统详解 (or AGENTS.md if that's where rules deployment strategy lives).

**Bumping versions**: `uv run install.py version --bump patch` (major/minor/patch). Updates `.cursor-plugin/{plugin,marketplace}.json`. Optional — see Claude Code Version-Gating above.

**Running tests**: `uv run pytest`. Tests use a scratch HOME and never touch `~/`. The golden test builds a copy of the repo and fails when the committed `_dist/` is stale — run `uv run install.py build` and commit `_dist/`. Installer code lives in `installer/` (one module per phase/platform); `install.py` is only the entrypoint.

**Adding a vendor submodule**: drop into `vendor/<name>/`, add to `.gitmodules`. For skill distribution, add a `third-party.json` entry with an `install` object.

## Debugging a Failed Build

```bash
# 1. Verify Python env
uv run python --version  # needs >=3.10

# 2. Dry-run build to surface errors without writing
uv run install.py build --dry-run

# 3. Check _dist/ contents
ls _dist/cursor/rules/ _dist/codex/

# 4. Check the Claude links
find ~/.claude/skills ~/.claude/agents -maxdepth 1 -type l ! -exec test -e {} \; -print  # dangling links

# 5. Check Codex AGENTS.md size budget
wc -c _dist/codex/AGENTS.md  # must be < 32KB
```

If `install.py build` fails with a stack trace, the issue is usually:

- A malformed YAML frontmatter in a rule (unclosed `---`)
- A `mcp.json` (source, repo root) with invalid JSON or `_platforms` syntax
