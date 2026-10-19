"""Committed plugin manifests: Claude and Cursor each load their own plugin."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _plugin_sources(manifest: Path) -> list[str]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return [plugin["source"] for plugin in data["plugins"]]


def test_claude_marketplace_never_exposes_the_repo_root():
    # Claude links skills/ and agents/ into ~/.claude. A plugin rooted at the
    # repo root would load every one of them a second time.
    sources = _plugin_sources(REPO / ".claude-plugin" / "marketplace.json")

    assert sources == ["./hooks/claude"]


def test_cursor_marketplace_has_its_own_manifest():
    # Cursor reads .cursor-plugin/marketplace.json; the Claude manifest above
    # must stay free to point somewhere else.
    sources = _plugin_sources(REPO / ".cursor-plugin" / "marketplace.json")

    assert sources == ["./"]


def test_claude_plugin_dir_ships_hooks_only():
    plugin_dir = REPO / "hooks" / "claude"

    assert (plugin_dir / ".claude-plugin" / "plugin.json").is_file()
    assert not (plugin_dir / "skills").exists()
    assert not (plugin_dir / "agents").exists()
