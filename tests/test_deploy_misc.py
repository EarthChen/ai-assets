"""Codex deploy, manual third-party skills, Claude plugin-cache pruning."""

from __future__ import annotations

import json

from conftest import make_skill

from installer import deploy_claude, deploy_codex, third_party


def test_codex_links_plugin_registers_once_and_copies_agents_md(sandbox):
    repo = sandbox.repo
    (repo / "_dist" / "codex").mkdir(parents=True)
    (repo / "_dist" / "codex" / "AGENTS.md").write_text("codex\n", encoding="utf-8")
    codex = sandbox.home / ".codex"
    codex.mkdir()
    (codex / "config.toml").write_text("model = 'x'\n", encoding="utf-8")

    deploy_codex.install_codex()
    deploy_codex.install_codex()  # idempotent: no duplicate registration

    plugin = codex / "plugins" / "local" / "earthchen-ai-assets"
    assert plugin.is_symlink() and plugin.resolve() == repo.resolve()
    assert (codex / "config.toml").read_text().count("[marketplaces.earthchen-ai-assets]") == 1
    assert (codex / "AGENTS.md").read_text(encoding="utf-8") == "codex\n"


def test_manual_skills_link_into_user_dirs(sandbox):
    repo = sandbox.repo
    make_skill(repo / "vendor" / "one", "s1")
    (repo / "third-party.json").write_text(json.dumps({"plugins": [
        {"name": "one", "install": {"source": "vendor/one", "generate": {
            "scan_dir": ".", "link_dir": "~/.agents/skills", "extra_links": ["~/.claude/skills"]}}},
        {"name": "remote-only", "platforms": {}},
    ]}), encoding="utf-8")

    third_party.install_manual_skills(name=None)

    target = (repo / "vendor" / "one" / "s1").resolve()
    for d in (".agents", ".claude"):
        assert (sandbox.home / d / "skills" / "s1").resolve() == target


def test_manual_skills_unknown_name_installs_nothing(sandbox, capsys):
    (sandbox.repo / "third-party.json").write_text(json.dumps({"plugins": []}), encoding="utf-8")
    third_party.install_manual_skills(name="missing")
    assert "no manual skill named 'missing'" in capsys.readouterr().out


def test_cache_prune_keeps_current_version_and_never_wipes_the_only_copy(sandbox):
    cache = sandbox.home / ".claude" / "plugins" / "cache" / "m" / "p"
    for ver in ("1.3.1", "1.3.2"):
        (cache / ver).mkdir(parents=True)

    deploy_claude._prune_claude_plugin_cache("p@m", "1.3.2")
    assert sorted(p.name for p in cache.iterdir()) == ["1.3.2"]

    # Keep-version snapshot missing (failed reinstall): delete nothing.
    deploy_claude._prune_claude_plugin_cache("p@m", "9.9.9")
    assert sorted(p.name for p in cache.iterdir()) == ["1.3.2"]
