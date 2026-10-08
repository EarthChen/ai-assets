# AI Plugins Repository

Unified AI agent assets across Claude Code, Codex, Cursor, and pi. Single source of truth for skills, agents, rules, MCP.

For repo maintenance (deploy pipeline, vendor submodule management, build transforms, diagnostic walkthroughs), see `CONTRIBUTING.md`. For end-user installation and usage, see `README.md`.

## Language rules migration

`rules/{java,python}/` were merged into `skills/java-development/references/` and `skills/python-development/references/` on 2026-09-04. Language-specific content now loads via skill description trigger, not globs auto-mount. `rules/common/` remains the only language-agnostic rule source.

## Architecture

```text
Source (single truth)     →  _dist/ (only platform-specific)  →  Plugin loads / Script deploys
rules/common/*.md              _dist/cursor/rules/**/*.mdc       .cursor-plugin (skills→./skills/, agents→./agents/)
rules/common/                  _dist/claude/rules/**/*.md        .claude-plugin (skills/agents 均省略→Claude 自动扫根, mcp)
mcp.json (_platforms tag)      _dist/codex/AGENTS.md             .codex-plugin (skills→./skills/, mcp)
global-instructions.md         _dist/codex/mcp.json
skills/      ──────────────────┐  (all 4 platforms scan repo-root skills/ directly;
agents/*.md  ──────────────────┘   NOT copied into _dist/ — root is committed
                                  real files only, no vendor symlinks to break)
pi/skills/ + pi/agents/ ─────── pi only (install_pi symlinks into ~/.pi/agent/{skills,agents}/;
                                  invisible to Claude/Codex/Cursor)
```

`_dist/` holds only what genuinely differs per platform: `mcp.json` (`_platforms` filter), `rules/` (`.mdc` vs `.md`), and the global-instructions deploy (`CLAUDE.md` / `AGENTS.md`). Skills and agents are read directly from the repo root by all four platforms — no per-platform copy.

## pi support (script-only deploy)

[pi](https://github.com/badlogic/pi-mono) has no plugin system compatible with this repo, so `install.py install --platform pi` deploys directly to `~/.pi/agent/`:

- **AGENTS.md**: `_dist/pi/AGENTS.md` (global-instructions + common rules, same embed as Codex; pi loads it from `~/.pi/agent/` at startup — no 32KB limit) → `~/.pi/agent/AGENTS.md`, **full overwrite** (repo is the single source of truth; my-pi-agent's own project docs live in that repo's CLAUDE.md)
- **Skills**: self-owned skills symlinked into `~/.agents/skills/` — pi scans that standard directory natively; same mechanism as the mattpocock/anysearch manual installs (which therefore need no extra work). Not registered via `settings.json`. Note: Codex also scans `~/.agents/skills/`, so it sees these links in addition to its plugin copy
- **pi-only skills**: `pi/skills/*` symlinked into `~/.pi/agent/skills/` — pi scans that dir recursively and no other harness scans it (unlike `~/.agents/skills/`, which Codex also reads), so these skills load exclusively on pi. Currently: none (`herdr-orchestration` moved to root `skills/` — it went multi-platform: orchestrator AND workers can run on pi, Claude Code, or Codex, mixed pools allowed)
- **Agents**: `agents/*.md` symlinked into `~/.pi/agent/agents/` — pi-subagents' `discoverAgents()` scans that user dir (alongside its builtins scout/reviewer/worker/...) and loads `*.md` with YAML frontmatter. Repo agent frontmatter only sets `name` + `description`; `model` and `tools` are intentionally omitted so pi-subagents inherits the parent session's model and grants the default tool set. Verify with `/subagents-doctor` + `subagent({ action: "list" })` after install.
- **pi-only agents**: `pi/agents/*.md` symlinked into the same `~/.pi/agent/agents/` dir — they sit outside the plugin-root `agents/` that Claude auto-scans and outside the `./agents/` path Cursor's manifest declares, so these load exclusively on pi. Currently: `Explore.md`
- **NOT deployed**: MCP (pi covers playwright etc. via its own extensions — no `mcp.json` sync), separate rules files (embedded in AGENTS.md; language rules via skills on demand)

## Update Mechanism

| Platform | Method | Trigger |
| --- | --- | --- |
| Cursor | `install.py install` (rsync real-dir, `--delete`) | After repo edits + restart/reload |
| Codex | Local symlink (instant, tracks repo) | After `build` |
| Claude Code | `install.py install` (local-directory marketplace, reinstall = fresh snapshot) | After `build` (when `_dist/` changed); bump optional |
| pi | `install.py install --platform pi` (direct deploy to `~/.pi/agent/`) | After `build` + install |

Headline caveats (full details in `CONTRIBUTING.md`):

- **Claude Code version-gating**: same `plugin.json` version → cached snapshot; reinstall forces fresh snapshot. Bump optional, diagnostic only.
- **Claude manifest declares no `agents`**: Claude auto-scans the plugin-root `agents/`; an `agents` key loads zero agents and `claude plugin validate` still passes (probe-verified on 2.1.285). Check reality with `claude plugin details earthchen-ai-assets@earthchen-ai-assets`.
- **Cursor local plugin is a real directory** (not symlink); Cursor's scanner skips symlinks in `~/.cursor/plugins/local/`.
- **Cursor marketplace has a stale-cache problem**; local real-dir wins over remote marketplace.
- **Cursor "Include third-party Plugins, Skills, and other configs": keep OFF** — recursive scan loads each skill ~11×.

## Single Source of Truth

This repo is the ONLY source for custom AI configuration. Do NOT place skills in `~/.agents/skills/` manually; do NOT install overlapping third-party plugins; all MCP servers managed in this repo's `mcp.json`.

## Rules Deployment Strategy

| Platform | User-level (always loaded) | Language rules (conditional) |
| --- | --- | --- |
| Cursor | `rules/common/*.mdc` (alwaysApply: true) | Auto-attached via `globs` field |
| Claude Code | `~/.claude/rules/common/` (no frontmatter needed) | Project `.claude/rules/` (paths field) |
| Codex | Embedded in `~/.codex/AGENTS.md` (common only, 32KB limit) | Via Skills on demand |

### Critical Platform Differences

- **Cursor**: uses `globs` field (NOT `paths`); extension must be `.mdc`
- **Claude Code user-level**: `paths` frontmatter is ignored (Bug #21858); rules always load unconditionally
- **Claude Code project-level**: `paths` works correctly for conditional loading
- **Codex**: no frontmatter support; 32KB limit on AGENTS.md; common rules only
- **Language rules** (Java, Python): migrated to skills on 2026-09-04 — see `skills/java-development/` and `skills/python-development/`. To add new language rules, create a `<lang>-development` skill rather than a `rules/<lang>/` directory.
