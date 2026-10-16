# AI Plugins Repository

Unified AI agent assets across Claude Code, Codex, Cursor, and pi. Single source of truth for skills, agents, rules, MCP.

Read `CONTRIBUTING.md` before touching the deploy pipeline, build transforms, vendor submodules, per-platform update triggers (`build` vs `install`), the pi deploy, or any plugin-loading failure. End-user installation and usage: `README.md`.

## Architecture

```text
Source (single truth)     →  _dist/ (only platform-specific)  →  Plugin loads / Script deploys
rules/common/*.md              _dist/cursor/rules/**/*.mdc       .cursor-plugin (agents→./agents/, rules+mcp→_dist/cursor/; no skills)
rules/common/                  _dist/claude/rules/**/*.md        Claude: ~/.claude/rules/common ◄── symlink (no plugin)
mcp.json (_platforms tag)      _dist/claude/mcp.json  ◄── load with `claude --mcp-config` (no user-scope link)
global-instructions.md         _dist/codex/AGENTS.md             Codex: AGENTS.md copy only (no plugin)
                               _dist/codex/mcp.json              (generated; no consumer)
skills/      ──────────────────┐  Claude: symlinks in ~/.claude/skills/. pi/Cursor/Codex: symlinks in ~/.agents/skills/
agents/*.md  ──────────────────┘  (one source per platform). Agents: Claude symlinks in ~/.claude/agents/, Cursor plugin, pi ~/.pi/agent/agents/.
                                  NOT copied into _dist/ — root is committed real files only
pi/skills/ + pi/agents/ ─────── pi only (install_pi symlinks into ~/.pi/agent/{skills,agents}/;
                                  invisible to Claude/Codex/Cursor)
```

Each platform loads self-owned skills from exactly one place: Claude from the `~/.claude/skills/` symlinks; pi, Cursor and Codex from the `~/.agents/skills/` symlinks. Cursor and Codex auto-discover a plugin's `skills/` and do not merge same-name skills, so the Cursor plugin copy omits `skills/` and Codex loads no repo plugin.

Code lives in `installer/`; `install.py` is a thin entrypoint. `uv run pytest` includes a golden test that fails when the committed `_dist/` is stale: run `uv run install.py build` after changing `rules/`, `global-instructions.md`, or `mcp.json`. `install` writes to `~`; run it only with the user's go-ahead.

## Gotchas

- **Single source of truth**: this repo is the ONLY source for custom AI configuration. Put skills here, not in `~/.agents/skills/`; skip overlapping third-party plugins; manage every MCP server in `mcp.json`.
- **Claude deploys by symlink, not plugin**: `install` links skills and agents (hot-reload, no reinstall after edits), `CLAUDE.md` and `rules/common` (read at session start, so edits need `build` and a new session). It uninstalls the legacy `earthchen-ai-assets` plugin, because a second copy loads every skill twice. Skill and agent names are bare, no `earthchen-ai-assets:` prefix.
- **Claude MCP has no link**: user-scope servers live in `~/.claude.json`, a runtime-state file. Load `_dist/claude/mcp.json` with `claude --mcp-config`; it holds no servers today.
- **`.claude-plugin/` stays for the Cursor marketplace** (it reads `marketplace.json`). `agents` must stay absent from `plugin.json` there too: the key loads zero agents (probe-verified on 2.1.285).
- **Cursor local plugin is a real directory**: Cursor's scanner skips symlinks in `~/.cursor/plugins/local/`. Local real-dir wins over the remote marketplace (stale cache).
- **Cursor "Include third-party Plugins, Skills, and other configs": keep OFF** — the recursive scan loads each skill ~11×.
- **Rules frontmatter differs per platform**: Cursor uses `globs` (NOT `paths`) and the `.mdc` extension. Claude Code user-level ignores `paths` (Bug #21858), so rules always load; project-level `paths` works. Codex has no frontmatter and a 32KB `AGENTS.md` limit; it embeds common rules only.
- **Language conventions live in skills**: `rules/{java,python}/` moved into `skills/<lang>-development/references/` on 2026-09-04 and load via skill-description trigger. Add a language by creating a `<lang>-development` skill; `rules/common/` stays the only language-agnostic rule source.
- **pi deploy is script-only** (`install.py install --platform pi`, details in `CONTRIBUTING.md`): `~/.pi/agent/AGENTS.md` is fully overwritten from `_dist/pi/AGENTS.md`; MCP is not deployed.
