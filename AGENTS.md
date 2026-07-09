# AI Plugins Repository

This repository manages unified AI agent assets across Claude Code, Codex, and Cursor.

## Development Guidelines

- Language: Chinese for communication, English for code/comments
- Package manager: `uv` for Python, `pnpm` for Node.js
- After modifying `rules/`, `mcp.json`, or `global-instructions.md`, run `uv run install.py` to regenerate `_dist/`
- Commit `_dist/` changes along with source changes

## Architecture

```
Source (single truth)     →  _dist/ (per-platform filtered)  →  Plugin loads
rules/*.md                    _dist/cursor/rules/*.mdc           .cursor-plugin
mcp.json (_platforms tag)     _dist/cursor/mcp.json              .claude-plugin
skills/                       _dist/claude/mcp.json              .codex-plugin
global-instructions.md        _dist/codex/...
```

## Key Files

- `install.py` - Build + deploy script
- `global-instructions.md` - Deployed as ~/.claude/CLAUDE.md and ~/.codex/AGENTS.md
- `rules/*.md` - YAML frontmatter with optional `platforms: [cursor]` for filtering
- `mcp.json` - `_platforms` field for per-platform MCP server filtering
- `third-party.json` - Third-party plugin references (not bundled)
