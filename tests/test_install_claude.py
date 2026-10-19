"""Claude Code deploy: symlinked skills, agents, CLAUDE.md and rules."""

from __future__ import annotations

import json
import subprocess

import pytest

from installer import deploy_claude

SELF_PLUGIN = "earthchen-ai-assets@earthchen-ai-assets"


def _declare_local_plugin(repo):
    (repo / "third-party.json").write_text(json.dumps({"plugins": [{
        "name": "other",
        "platforms": {"claude": {
            "marketplace_ref": "https://example.invalid/other.git",
            "marketplace_source": "local",
            "plugin_id": "other@other",
        }},
    }]}), encoding="utf-8")


def _seed_repo(repo):
    (repo / "skills" / "alpha").mkdir(parents=True)
    (repo / "skills" / "alpha" / "SKILL.md").write_text("alpha\n", encoding="utf-8")
    (repo / "agents").mkdir()
    (repo / "agents" / "reviewer.md").write_text("reviewer\n", encoding="utf-8")
    (repo / "rules" / "common").mkdir(parents=True)
    (repo / "global-instructions.md").write_text("global\n", encoding="utf-8")
    (repo / "rules" / "common" / "r.md").write_text("rule\n", encoding="utf-8")


@pytest.fixture
def fake_cli(empty_path, monkeypatch):
    """A `claude` binary on PATH; records calls and answers `plugin list`."""
    binary = empty_path / "claude"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    state = {"calls": [], "listed": ""}

    def fake_run(cmd, **kwargs):
        state["calls"].append(cmd)
        stdout = state["listed"] if cmd[:3] == ["claude", "plugin", "list"] else ""
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return state


def test_files_deploy_as_symlinks_into_repo(sandbox, empty_path):
    # Edits to skills/, agents/ and the generated _dist files must reach Claude
    # without a reinstall, so every asset is a link, never a copy.
    _seed_repo(sandbox.repo)
    claude_home = sandbox.home / ".claude"

    deploy_claude.install_claude(dry_run=False)

    assert (claude_home / "skills" / "alpha").is_symlink()
    assert (claude_home / "skills" / "alpha" / "SKILL.md").read_text() == "alpha\n"
    assert (claude_home / "agents" / "reviewer.md").resolve() == (sandbox.repo / "agents" / "reviewer.md")
    assert (claude_home / "CLAUDE.md").resolve() == sandbox.repo / "global-instructions.md"
    assert (claude_home / "rules" / "common").resolve() == sandbox.repo / "rules" / "common"
    assert (claude_home / "rules" / "common" / "r.md").read_text() == "rule\n"


def test_missing_claude_cli_logs_why_plugin_steps_were_skipped(sandbox, empty_path, capsys):
    _seed_repo(sandbox.repo)
    deploy_claude.install_claude(dry_run=False)
    assert "claude CLI not on PATH" in capsys.readouterr().out
    assert (sandbox.home / ".claude" / "skills" / "alpha").is_symlink()


def test_stale_skill_and_agent_links_are_removed_but_foreign_links_stay(sandbox, empty_path):
    _seed_repo(sandbox.repo)
    claude_home = sandbox.home / ".claude"
    (claude_home / "skills").mkdir(parents=True)
    (claude_home / "agents").mkdir()
    gone_skill = sandbox.repo / "skills" / "gone"  # removed from the repo
    gone_agent = sandbox.repo / "agents" / "gone.md"
    (claude_home / "skills" / "gone").symlink_to(gone_skill)
    (claude_home / "agents" / "gone.md").symlink_to(gone_agent)
    vendor = sandbox.home / "vendor-skill"
    vendor.mkdir()
    (claude_home / "skills" / "vendor").symlink_to(vendor)

    deploy_claude.install_claude(dry_run=False)

    assert not (claude_home / "skills" / "gone").is_symlink()
    assert not (claude_home / "agents" / "gone.md").is_symlink()
    assert (claude_home / "skills" / "vendor").is_symlink()


def test_real_agent_file_is_never_overwritten(sandbox, empty_path, capsys):
    _seed_repo(sandbox.repo)
    agents = sandbox.home / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "reviewer.md").write_text("mine\n", encoding="utf-8")

    deploy_claude.install_claude(dry_run=False)

    assert (agents / "reviewer.md").read_text() == "mine\n"
    assert not (agents / "reviewer.md").is_symlink()
    assert "WARNING" in capsys.readouterr().out


def test_previous_copy_of_claude_md_is_replaced_by_link(sandbox, empty_path):
    _seed_repo(sandbox.repo)
    claude_home = sandbox.home / ".claude"
    claude_home.mkdir()
    (claude_home / "CLAUDE.md").write_text("global\n", encoding="utf-8")  # old deploy copy

    deploy_claude.install_claude(dry_run=False)

    assert (claude_home / "CLAUDE.md").resolve() == sandbox.repo / "global-instructions.md"
    assert not (claude_home / "CLAUDE.md.pre-link.bak").exists()


def test_hand_edited_claude_md_is_kept_as_backup(sandbox, empty_path):
    _seed_repo(sandbox.repo)
    claude_home = sandbox.home / ".claude"
    claude_home.mkdir()
    (claude_home / "CLAUDE.md").write_text("hand edit\n", encoding="utf-8")

    deploy_claude.install_claude(dry_run=False)

    assert (claude_home / "CLAUDE.md").is_symlink()
    assert (claude_home / "CLAUDE.md.pre-link.bak").read_text() == "hand edit\n"


def test_previous_rules_copy_is_replaced_by_directory_link(sandbox, empty_path):
    _seed_repo(sandbox.repo)
    old = sandbox.home / ".claude" / "rules" / "common"
    old.mkdir(parents=True)
    (old / "stale.md").write_text("stale\n", encoding="utf-8")

    deploy_claude.install_claude(dry_run=False)

    assert old.is_symlink()
    assert old.resolve() == sandbox.repo / "rules" / "common"
    assert not (old / "stale.md").exists()


def test_dry_run_writes_nothing(sandbox, empty_path):
    _seed_repo(sandbox.repo)
    deploy_claude.install_claude(dry_run=True)
    assert not (sandbox.home / ".claude").exists()


def test_unrelated_plugins_are_never_uninstalled(sandbox, fake_cli):
    _seed_repo(sandbox.repo)
    fake_cli["listed"] = "  ❯ context-mode@context-mode\n"

    deploy_claude.install_claude(dry_run=False)

    assert not [c for c in fake_cli["calls"] if "uninstall" in c or "remove" in c]


def test_other_third_party_plugins_still_install(sandbox, fake_cli):
    _declare_local_plugin(sandbox.repo)
    _seed_repo(sandbox.repo)

    deploy_claude.install_claude(dry_run=False)

    assert ["claude", "plugin", "install", "other@other", "--scope", "user"] in fake_cli["calls"]


def _seed_hooks_plugin(repo):
    manifest = repo / "hooks" / "claude" / ".claude-plugin"
    manifest.mkdir(parents=True)
    (manifest / "plugin.json").write_text(
        json.dumps({"name": "earthchen-ai-assets", "version": "1.4.0"}), encoding="utf-8"
    )


def test_hooks_plugin_installs_from_the_repo_marketplace(sandbox, fake_cli):
    _seed_repo(sandbox.repo)
    _seed_hooks_plugin(sandbox.repo)

    deploy_claude.install_claude(dry_run=False)

    assert ["claude", "plugin", "marketplace", "add", str(sandbox.repo)] in fake_cli["calls"]
    assert ["claude", "plugin", "install", SELF_PLUGIN, "--scope", "user"] in fake_cli["calls"]


def test_earlier_install_of_the_same_id_is_reinstalled_not_retired(sandbox, fake_cli):
    # The repo marketplace now lists only the hooks-only plugin, so an install
    # left from the full plugin needs a reinstall to switch content: `plugin
    # update` skips an unchanged version. Removing the marketplace would
    # take the new plugin down with it.
    _seed_repo(sandbox.repo)
    _seed_hooks_plugin(sandbox.repo)
    fake_cli["listed"] = f"  ❯ {SELF_PLUGIN}\n    Version: 1.3.2\n"

    deploy_claude.install_claude(dry_run=False)

    calls = fake_cli["calls"]
    assert ["claude", "plugin", "uninstall", SELF_PLUGIN] in calls
    assert ["claude", "plugin", "install", SELF_PLUGIN, "--scope", "user"] in calls
    assert not [c for c in calls if c[:4] == ["claude", "plugin", "marketplace", "remove"]]


def test_hooks_plugin_is_skipped_when_its_directory_is_absent(sandbox, fake_cli):
    _seed_repo(sandbox.repo)

    deploy_claude.install_claude(dry_run=False)

    assert not [c for c in fake_cli["calls"] if SELF_PLUGIN in c]


def test_dry_run_makes_no_hooks_plugin_calls(sandbox, fake_cli):
    _seed_repo(sandbox.repo)
    _seed_hooks_plugin(sandbox.repo)

    deploy_claude.install_claude(dry_run=True)

    assert not [c for c in fake_cli["calls"] if c[2:3] in (["install"], ["uninstall"]) or "add" in c]
