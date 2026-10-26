"""Codex deploy, manual third-party skills, Claude plugin-cache pruning."""

from __future__ import annotations

import json

from conftest import link, make_skill

from installer import deploy_claude, deploy_codex, third_party


def test_codex_copies_agents_md_without_registering_a_plugin(sandbox):
    # Codex gets self-owned skills from ~/.agents/skills; the repo plugin
    # carried only skills (+ an empty MCP file) and loaded them twice.
    repo = sandbox.repo
    (repo / "_dist" / "codex").mkdir(parents=True)
    (repo / "_dist" / "codex" / "AGENTS.md").write_text("codex\n", encoding="utf-8")
    codex = sandbox.home / ".codex"
    codex.mkdir()
    (codex / "config.toml").write_text("model = 'x'\n", encoding="utf-8")

    deploy_codex.install_codex()

    assert not (codex / "plugins" / "local" / "earthchen-ai-assets").exists()
    assert (codex / "config.toml").read_text(encoding="utf-8") == "model = 'x'\n"
    assert (codex / "AGENTS.md").read_text(encoding="utf-8") == "codex\n"


def test_codex_disables_previously_registered_plugin_and_removes_its_link(sandbox):
    repo = sandbox.repo
    codex = sandbox.home / ".codex"
    link(codex / "plugins" / "local" / "earthchen-ai-assets", repo)
    config = (
        "model = 'x'\n"
        "\n[plugins.\"earthchen-ai-assets@earthchen-ai-assets\"]\n"
        "enabled = true\n"
        "\n[plugins.\"other@market\"]\n"
        "enabled = true\n"
    )
    (codex / "config.toml").write_text(config, encoding="utf-8")

    deploy_codex.install_codex()

    assert not (codex / "plugins" / "local" / "earthchen-ai-assets").is_symlink()
    assert (codex / "config.toml").read_text(encoding="utf-8") == config.replace(
        "earthchen-ai-assets\"]\nenabled = true", "earthchen-ai-assets\"]\nenabled = false")


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


def _write_local_source_entry(repo, local):
    (repo / "third-party.json").write_text(json.dumps({"plugins": [
        {"name": "one", "install": {"source": "vendor/one", "local_source": str(local), "generate": {
            "scan_dir": ".", "link_dir": "~/.claude/skills"}}},
    ]}), encoding="utf-8")


def test_manual_skills_prefer_local_source_so_dev_checkout_edits_apply_at_once(sandbox, tmp_path):
    # The CLIs run from an editable install of the dev checkout; linking the
    # skill to the same checkout keeps docs and CLI behavior in step.
    make_skill(sandbox.repo / "vendor" / "one", "s1")
    local = tmp_path / "dev" / "one"
    make_skill(local, "s1")
    _write_local_source_entry(sandbox.repo, local)

    third_party.install_manual_skills(name=None)

    assert (sandbox.home / ".claude" / "skills" / "s1").resolve() == (local / "s1").resolve()


def test_manual_skills_fall_back_to_vendor_when_local_source_is_absent(sandbox, tmp_path):
    # local_source is a path on one machine; every other clone must keep
    # working from the pinned submodule.
    make_skill(sandbox.repo / "vendor" / "one", "s1")
    _write_local_source_entry(sandbox.repo, tmp_path / "missing")

    third_party.install_manual_skills(name=None)

    target = (sandbox.repo / "vendor" / "one" / "s1").resolve()
    assert (sandbox.home / ".claude" / "skills" / "s1").resolve() == target


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
