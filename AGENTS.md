# AI Plugins Repository

Unified AI agent assets across Claude Code, Codex, Cursor, and pi. Single source of truth for skills, agents, rules, MCP.

For repo maintenance (deploy pipeline, vendor submodule management, build transforms, diagnostic walkthroughs), see `CONTRIBUTING.md`. For end-user installation and usage, see `README.md`.

## Language rules migration

`rules/{java,python}/` were merged into `skills/java-development/references/` and `skills/python-development/references/` on 2026-09-04. Language-specific content now loads via skill description trigger, not globs auto-mount. `rules/common/` remains the only language-agnostic rule source.

## Architecture

```text
Source (single truth)     →  _dist/ (only platform-specific)  →  Plugin loads / Script deploys
rules/common/*.md              _dist/cursor/rules/**/*.mdc       .cursor-plugin (skills→./skills/, agents→./agents/, rules+mcp→_dist/cursor/)
rules/common/                  _dist/claude/rules/**/*.md        .claude-plugin (skills/agents 均省略→Claude 自动扫根, mcp→.mcp.json)
mcp.json (_platforms tag)      _dist/claude/mcp.json  ◄── .mcp.json symlink, read by Claude AND Codex
global-instructions.md         _dist/codex/AGENTS.md             .codex-plugin (skills→./skills/, mcpServers→./.mcp.json)
                               _dist/codex/mcp.json              (generated; no consumer)
skills/      ──────────────────┐  (Cursor/Claude/Codex read repo-root skills/ directly; pi via
agents/*.md  ──────────────────┘   symlinks in ~/.pi/agent/{skills,agents}/. NOT copied into _dist/ —
                                  root is committed real files only, no vendor symlinks to break)
pi/skills/ + pi/agents/ ─────── pi only (install_pi symlinks into ~/.pi/agent/{skills,agents}/;
                                  invisible to Claude/Codex/Cursor)
```

`_dist/` holds only what genuinely differs per platform: `mcp.json` (`_platforms` filter), `rules/` (`.mdc` vs `.md`), and the global-instructions deploy (`CLAUDE.md` / `AGENTS.md`). Skills and agents are read directly from the repo root by all four platforms (pi through symlinks) — no per-platform copy. Codex has no MCP file of its own: its manifest points at `./.mcp.json`, the same `_dist/claude/mcp.json` Claude reads (see `CONTRIBUTING.md`).

`install.py` is a thin entrypoint; the code lives in `installer/` (`build.py`, `deploy_{claude,codex,cursor,pi}.py`, `third_party.py`, `version.py`, `cli.py`; `paths.py` holds every filesystem location). Tests: `uv run pytest` (includes a golden test that fails when the committed `_dist/` is stale).

## pi support (script-only deploy)

[pi](https://github.com/badlogic/pi-mono) has no plugin system compatible with this repo, so `install.py install --platform pi` deploys directly to `~/.pi/agent/`:

- **AGENTS.md**: `_dist/pi/AGENTS.md` (global-instructions + common rules, same embed as Codex; pi loads it from `~/.pi/agent/` at startup — no 32KB limit) → `~/.pi/agent/AGENTS.md`, **full overwrite** (repo is the single source of truth; my-pi-agent's own project docs live in that repo's CLAUDE.md)
- **Skills**: self-owned skills (`skills/*`) symlinked into `~/.pi/agent/skills/` — pi scans that dir recursively and no other harness reads it. Not registered via `settings.json`. They are NOT linked into `~/.agents/skills/`: Codex and Cursor also scan that dir and already get these skills from their plugin, so links there loaded every skill twice. `~/.agents/skills/` holds only the third-party links from `install.py manual` (mattpocock, anysearch, ...), which pi also scans natively. `install.py install` removes legacy links from `~/.agents/skills/` that resolve into this repo's `skills/` (skipped by a `--platform` run that excludes a detected pi, since those links stay pi's skill source until pi is reinstalled); vendor links and real directories stay
- **pi-only skills**: `pi/skills/*` symlinked into the same `~/.pi/agent/skills/` — outside the plugin-root `skills/`, so these skills load exclusively on pi. Stale-link cleanup in that shared dir is scoped per source (`skills/` vs `pi/skills/`). Currently: none (`herdr-orchestration` moved to root `skills/` — it went multi-platform: orchestrator AND workers can run on pi, Claude Code, or Codex, mixed pools allowed)
- **Agents**: `agents/*.md` symlinked into `~/.pi/agent/agents/` — pi-subagents' `discoverAgents()` scans that user dir (alongside its builtins scout/reviewer/worker/...) and loads `*.md` with YAML frontmatter. Repo agent frontmatter only sets `name` + `description`; `model` and `tools` are intentionally omitted so pi-subagents inherits the parent session's model and grants the default tool set. Verify with `/subagents-doctor` + `subagent({ action: "list" })` after install.
- **pi-only agents**: `pi/agents/*.md` symlinked into the same `~/.pi/agent/agents/` dir — they sit outside the plugin-root `agents/` that Claude auto-scans and outside the `./agents/` path Cursor's manifest declares, so these load exclusively on pi. Currently: `Explore.md`
- **NOT deployed**: MCP (pi covers playwright etc. via its own extensions — no `mcp.json` sync), separate rules files (embedded in AGENTS.md; language conventions via `skills/<lang>-development` on demand)

## Update Mechanism

| Platform | Method | Trigger |
| --- | --- | --- |
| Cursor | `install.py install` (rsync real-dir, `--delete`) | After repo edits: `install` (+ `build` first if rules/MCP changed) + restart/reload |
| Codex | Plugin symlink (skills instant, tracks repo); `~/.codex/AGENTS.md` is a copy | Skills: none. AGENTS.md: `build` + `install` |
| Claude Code | `install.py install` (local-directory marketplace, reinstall = fresh snapshot) | After repo edits: `install` (+ `build` first if `_dist/` inputs changed); bump optional |
| pi | `install.py install --platform pi` (AGENTS.md copy + skill/agent symlinks under `~/.pi/agent/`) | AGENTS.md: `build` + `install`; skill/agent edits instant, new/renamed ones need `install` |

Headline caveats (full details in `CONTRIBUTING.md`):

- **Claude Code version-gating**: same `plugin.json` version → cached snapshot; reinstall forces fresh snapshot. Bump optional, diagnostic only.
- **Claude manifest declares no `agents`**: Claude auto-scans the plugin-root `agents/`; an `agents` key loads zero agents and `claude plugin validate` still passes (probe-verified on 2.1.285). Check reality with `claude plugin details earthchen-ai-assets@earthchen-ai-assets`.
- **Cursor local plugin is a real directory** (not symlink); Cursor's scanner skips symlinks in `~/.cursor/plugins/local/`.
- **Cursor marketplace has a stale-cache problem**; local real-dir wins over remote marketplace.
- **Cursor "Include third-party Plugins, Skills, and other configs": keep OFF** — recursive scan loads each skill ~11×.

## Single Source of Truth

This repo is the ONLY source for custom AI configuration. Do NOT place skills in `~/.agents/skills/` manually; do NOT install overlapping third-party plugins; all MCP servers managed in this repo's `mcp.json`.

## Rules Deployment Strategy

| Platform | User-level (always loaded) |
| --- | --- |
| Cursor | `rules/common/*.mdc` (alwaysApply: true) |
| Claude Code | `~/.claude/rules/common/` (no frontmatter needed) |
| Codex | Embedded in `~/.codex/AGENTS.md` (common only, 32KB limit) |

Language conventions are not rules: every platform loads them on demand from `skills/<lang>-development/`.

### Critical Platform Differences

- **Cursor**: uses `globs` field (NOT `paths`); extension must be `.mdc`
- **Claude Code user-level**: `paths` frontmatter is ignored (Bug #21858); rules always load unconditionally
- **Claude Code project-level**: `paths` works correctly for conditional loading
- **Codex**: no frontmatter support; 32KB limit on AGENTS.md; common rules only
- **Language rules** (Java, Python): migrated to skills on 2026-09-04 — see `skills/java-development/` and `skills/python-development/`. To add new language rules, create a `<lang>-development` skill rather than a `rules/<lang>/` directory.
