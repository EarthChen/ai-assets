"""In-process build: per-platform `_dist/` layout and manifest guard.

The golden test proves byte equality for the real inputs; these tests pin the
per-platform routing rules on small inputs, where a failure names the rule.
"""

from __future__ import annotations

import json

from conftest import link, make_skill

from installer import build


def _write_build_inputs(repo):
    common = repo / "rules" / "common"
    common.mkdir(parents=True)
    (common / "style.md").write_text("# Style\n", encoding="utf-8")
    (common / "cursor-only.md").write_text(
        "---\nplatforms: [cursor]\n---\n# Cursor only\n", encoding="utf-8")
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
    assert sorted(p.name for p in (dist / "cursor" / "rules" / "common").iterdir()) == [
        "cursor-only.mdc", "style.mdc"]
    assert (dist / "cursor" / "rules" / "global-instructions.mdc").is_file()
    # Claude: platform-filtered .md rules plus CLAUDE.md.
    assert [p.name for p in (dist / "claude" / "rules" / "common").iterdir()] == ["style.md"]
    assert (dist / "claude" / "CLAUDE.md").read_text(encoding="utf-8") == "# Global\n"
    # Codex/pi: one AGENTS.md embedding the applicable common rules.
    for platform in ("codex", "pi"):
        agents = (dist / platform / "AGENTS.md").read_text(encoding="utf-8")
        assert agents == "# Global\n\n\n# --- Rules ---\n\n# Style\n"
    # MCP: always written for plugin platforms (manifests point at it), never for pi.
    assert json.loads((dist / "claude" / "mcp.json").read_text()) == {"mcpServers": {}}
    assert json.loads((dist / "cursor" / "mcp.json").read_text()) == {
        "mcpServers": {"fb": {"command": "uvx"}}}
    assert not (dist / "pi" / "mcp.json").exists()


def test_build_dry_run_writes_nothing(sandbox):
    _write_build_inputs(sandbox.repo)
    build.build_dist(dry_run=True)
    assert not (sandbox.repo / "_dist").exists()


def test_build_strips_agents_key_from_claude_manifest(sandbox):
    # A manifest `agents` key makes Claude load zero agents (it overrides the
    # plugin-root auto-scan), and `claude plugin validate` does not catch it.
    repo = sandbox.repo
    _write_build_inputs(repo)
    manifest = repo / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"name": "p", "agents": ["./agents/x.md"]}), encoding="utf-8")

    build.build_dist()

    assert json.loads(manifest.read_text(encoding="utf-8")) == {"name": "p"}


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
