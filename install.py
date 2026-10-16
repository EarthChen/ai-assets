#!/usr/bin/env python3
"""
Unified AI agent assets installer.

Two-phase deployment:
  Phase 1 (build): Generate platform-filtered content in _dist/
  Phase 2 (deploy): Install plugin links (symlink for Codex, real-dir copy for Cursor)

Plugin systems handle (skills/ and agents/ are read from the repo root,
not from _dist/):
  - Cursor: skills/, agents/, rules + MCP from _dist/cursor/
  - Codex: skills/ (no MCP consumer for _dist/codex/mcp.json)

Script handles (things plugins can't do):
  - Claude Code: symlinks ~/.claude/{skills,agents,CLAUDE.md,rules/common}
    into the repo (no MCP deploy)
  - Codex: AGENTS.md
  - pi: no plugin system — script deploys AGENTS.md (full overwrite),
    symlinks skills/ + pi/skills/ into ~/.pi/agent/skills/ and agents/ +
    pi/agents/ into ~/.pi/agent/agents/ (MCP not synced: pi covers it via
    its own extensions)
  - All: plugin links (Codex symlink, Cursor real-dir copy)

Usage:
    uv run install.py                         # build + install (all platforms)
    uv run install.py build                   # only regenerate _dist/
    uv run install.py install --platform X    # install + third-party skills
    uv run install.py manual [name]           # reinstall just one 3rd-party skill
    uv run install.py version 1.2.0           # set version across all plugins
    uv run install.py version --bump patch    # bump version (major/minor/patch)
"""

from installer.cli import main

if __name__ == "__main__":
    main()
