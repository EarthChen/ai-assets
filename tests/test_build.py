"""In-process build: per-platform `_dist/` layout and manifest guard.

The golden test proves byte equality for the real inputs; these tests pin the
per-platform routing rules on small inputs, where a failure names the rule.
"""

from __future__ import annotations

import json

import pytest
from conftest import link, make_skill

from installer import build


def _write_build_inputs(repo):
    common = repo / "rules" / "common"
    common.mkdir(parents=True)
    (common / "style.md").write_text("# Style\n", encoding="utf-8")
    cursor = repo / "rules" / "cursor"
    cursor.mkdir()
    (cursor / "cursor-only.md").write_text("# Cursor only\n", encoding="utf-8")
    # The directory alone names the platform; no frontmatter field repeats it.
    claude = repo / "rules" / "claude"
    claude.mkdir()
    (claude / "claude-only.md").write_text("# Claude only\n", encoding="utf-8")
    codex = repo / "rules" / "codex"
    codex.mkdir()
    (codex / "codex-only.md").write_text("# Codex only\n", encoding="utf-8")
    (repo / "global-instructions.md").write_text("# Global\n", encoding="utf-8")
    (repo / "mcp.json").write_text(json.dumps({"mcpServers": {
        "fb": {"command": "uvx", "_platforms": ["cursor"]},
    }}), encoding="utf-8")
    vendor = repo / "vendor" / "mattpocock-skills"
    vendor.mkdir(parents=True)
    (vendor / ".placeholder").write_text("", encoding="utf-8")


def test_build_routes_rules_instructions_and_mcp_per_platform(sandbox):
    repo = sandbox.repo
    _write_build_inputs(repo)

    build.build_dist()

    dist = repo / "_dist"
    # Cursor: every applicable rule as .mdc, global instructions as a rule.
    assert (dist / "cursor" / "rules" / "common" / "style.mdc").is_file()
    assert (dist / "cursor" / "rules" / "cursor" / "cursor-only.mdc").is_file()
    assert (dist / "cursor" / "rules" / "global-instructions.mdc").is_file()
    # A Claude-only rule reaches no other platform.
    assert not (dist / "cursor" / "rules" / "claude").exists()
    # Claude links rules/common and global-instructions.md from the repo, so
    # _dist/claude holds neither.
    assert not (dist / "claude" / "rules").exists()
    assert not (dist / "claude" / "CLAUDE.md").exists()
    assert not (dist / "cursor" / "rules" / "codex").exists()
    # Codex/pi: one AGENTS.md embedding rules/common plus the platform's own dir.
    assert (dist / "codex" / "AGENTS.md").read_text(encoding="utf-8") == (
        "# Global\n\n\n# --- Rules ---\n\n# Style\n\n\n# Codex only\n")
    assert (dist / "pi" / "AGENTS.md").read_text(encoding="utf-8") == (
        "# Global\n\n\n# --- Rules ---\n\n# Style\n")
    # MCP: written for cursor and codex, never for claude (no MCP deploy) or pi.
    assert not (dist / "claude").exists()
    assert json.loads((dist / "cursor" / "mcp.json").read_text()) == {
        "mcpServers": {"fb": {"command": "uvx"}}}
    assert not (dist / "pi" / "mcp.json").exists()


@pytest.mark.parametrize("subdir", ["common", "claude"])
def test_build_rejects_rule_with_platforms_field(sandbox, subdir):
    # The directory routes a rule. A leftover `platforms` field would be
    # ignored, so the rule would load where its author did not intend.
    _write_build_inputs(sandbox.repo)
    (sandbox.repo / "rules" / subdir / "bad.md").write_text(
        "---\nplatforms: [cursor]\n---\n# Bad\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="bad.md"):
        build.build_dist()


def test_build_dry_run_writes_nothing(sandbox):
    _write_build_inputs(sandbox.repo)
    build.build_dist(dry_run=True)
    assert not (sandbox.repo / "_dist").exists()


def test_build_removes_stale_mattpocock_links_from_skills_only(sandbox):
    repo = sandbox.repo
    _write_build_inputs(repo)
    vendor = repo / "vendor" / "mattpocock-skills"
    (vendor / ".claude-plugin").mkdir()
    (vendor / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"skills": ["./skills/engineering/tdd", "./skills/engineering/own"]}),
        encoding="utf-8")
    tdd = make_skill(vendor / "skills" / "engineering", "tdd")
    link(repo / "skills" / "tdd", tdd)
    own = make_skill(repo / "elsewhere", "own")
    link(repo / "skills" / "own", own)  # same name, not a mattpocock link

    build.build_dist()

    assert sorted(p.name for p in (repo / "skills").iterdir()) == ["own"]
