"""MCP platform filtering and plugin version management."""

from __future__ import annotations

import json

import pytest

from installer import build, version


def test_filter_mcp_for_platform_keeps_untagged_and_matching_servers(sandbox):
    (sandbox.repo / "mcp.json").write_text(json.dumps({"mcpServers": {
        "everywhere": {"command": "a"},
        "cursor-only": {"command": "b", "_platforms": ["cursor"]},
    }}), encoding="utf-8")
    # `_platforms` is a build-time tag: it selects servers and must not leak
    # into the platform file.
    assert build.filter_mcp_for_platform("cursor") == {
        "everywhere": {"command": "a"},
        "cursor-only": {"command": "b"},
    }
    assert build.filter_mcp_for_platform("claude") == {"everywhere": {"command": "a"}}


def test_filter_mcp_for_platform_without_source_file_is_empty(sandbox):
    assert build.filter_mcp_for_platform("claude") == {}


@pytest.mark.parametrize(("current", "part", "expected"), [
    ("1.3.2", "patch", "1.3.3"),
    ("1.3.2", "minor", "1.4.0"),
    ("1.3.2", "major", "2.0.0"),
    ("1.3", "patch", "1.3.1"),
])
def test_bump_version(current, part, expected):
    assert version._bump_version(current, part) == expected


def test_get_current_version_uses_highest_manifest_version(sandbox):
    # Drifted manifests must not let a bump re-issue an existing version.
    versions = {".cursor-plugin": "1.3.0", ".claude-plugin": "1.3.10", ".codex-plugin": "1.3.2"}
    for d, ver in versions.items():
        (sandbox.repo / d).mkdir()
        (sandbox.repo / d / "plugin.json").write_text(json.dumps({"version": ver}), encoding="utf-8")
    assert version._get_current_version() == "1.3.10"


def test_get_current_version_without_manifests_is_zero(sandbox):
    assert version._get_current_version() == "0.0.0"
