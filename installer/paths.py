"""Filesystem locations the installer reads and writes.

Every module reads these as `paths.NAME` at call time, so a test redirects
the whole installer by patching this one module.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
DIST = REPO_ROOT / "_dist"

CLAUDE_HOME = HOME / ".claude"
CODEX_HOME = HOME / ".codex"
CURSOR_HOME = HOME / ".cursor"
AGENTS_HOME = HOME / ".agents"
PI_AGENT_HOME = HOME / ".pi" / "agent"

THIRD_PARTY_JSON = REPO_ROOT / "third-party.json"

PLUGIN_JSONS = [
    REPO_ROOT / ".cursor-plugin" / "plugin.json",
]

MARKETPLACE_JSON = REPO_ROOT / ".cursor-plugin" / "marketplace.json"
