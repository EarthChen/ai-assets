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
| Cursor | Local symlink (instant) | After `build` |
| Codex | Local symlink (instant) | After `build` |
| Claude Code | ref-tracked auto-pull | Each session start (fetches main branch HEAD) |

Claude Code's `marketplace.json` uses `ref: "main"` without SHA pinning.
No manual `claude plugin update` needed; push to main → next session picks it up.

## Single Source of Truth

This repo is the ONLY source for custom AI configuration:
- Do NOT place skills in `~/.agents/skills/` manually
- Do NOT install third-party plugins that overlap with this repo
- All MCP servers managed in this repo's `mcp.json`

## mattpocock/skills (hybrid management)

Engineering skills from [mattpocock/skills](https://github.com/mattpocock/skills), aligned to the 21 skills declared in upstream `vendor/mattpocock-skills/.claude-plugin/plugin.json`. **Hybrid management** because mattpocock ships only a Claude native plugin (no Codex/Cursor plugin):

- **Claude Code**: provided by the native plugin `mattpocock-skills@mattpocock`. `install.py build` excludes these vendored skills from the Claude distribution so they aren't duplicated.
- **Codex / Cursor**: vendored as a git submodule at `vendor/mattpocock-skills/`, symlinked into `skills/`. Codex deep-copies them into `_dist/codex/skills/` at build; Cursor reads `skills/` directly.

After cloning, run `git submodule update --init` to initialize (needed for Codex/Cursor).

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

### Build Transforms

| Source field | → Cursor | → Claude Code | → Codex |
|---|---|---|---|
| `paths: [...]` | `globs: [...]` (JSON array) | `paths: csv` (CSV string + alwaysApply: false) | stripped (plain text) |
| `globs: [...]` | kept as JSON array | → `paths: csv` (converted + alwaysApply: false) | stripped |
| `platforms: [...]` | removed | removed | used for filtering then stripped |
| `description` | kept | kept | stripped |
| `alwaysApply` | kept | kept | stripped |

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
