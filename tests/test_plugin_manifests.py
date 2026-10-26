"""Committed plugin manifests: only Cursor loads a repo plugin."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _plugin_sources(manifest: Path) -> list[str]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return [plugin["source"] for plugin in data["plugins"]]


def test_repo_ships_no_claude_marketplace():
    # Claude links skills/ and agents/ into ~/.claude. A Claude plugin rooted
    # at the repo root would load every one of them a second time.
    assert not (REPO / ".claude-plugin").exists()


def test_cursor_marketplace_has_its_own_manifest():
    # Cursor reads .cursor-plugin/marketplace.json; the Claude manifest above
    # must stay free to point somewhere else.
    sources = _plugin_sources(REPO / ".cursor-plugin" / "marketplace.json")

    assert sources == ["./"]
