"""Claude Code deploy."""

from __future__ import annotations

import json
import subprocess

from installer import deploy_claude


def _declare_local_self_plugin(repo):
    (repo / "third-party.json").write_text(json.dumps({"plugins": [{
        "name": "self",
        "platforms": {"claude": {
            "marketplace_ref": "https://example.invalid/self.git",
            "marketplace_source": "local",
            "plugin_id": "self@self",
        }},
    }]}), encoding="utf-8")


def test_missing_claude_cli_skips_plugin_steps_but_still_deploys_files(sandbox, empty_path):
    # detect_platforms() reports Claude present from ~/.claude alone, so the
    # installer runs on machines without the `claude` binary. It must not
    # crash there: plugin steps need the CLI, CLAUDE.md and rules do not.
    _declare_local_self_plugin(sandbox.repo)
    dist = sandbox.repo / "_dist" / "claude"
    (dist / "rules" / "common").mkdir(parents=True)
    (dist / "CLAUDE.md").write_text("global\n", encoding="utf-8")
    (dist / "rules" / "common" / "r.md").write_text("rule\n", encoding="utf-8")
    (sandbox.home / ".claude").mkdir()

    deploy_claude.install_claude(dry_run=False)

    claude_home = sandbox.home / ".claude"
    assert (claude_home / "CLAUDE.md").read_text(encoding="utf-8") == "global\n"
    assert (claude_home / "rules" / "common" / "r.md").read_text(encoding="utf-8") == "rule\n"


def test_missing_claude_cli_logs_why_plugins_were_skipped(sandbox, empty_path, capsys):
    _declare_local_self_plugin(sandbox.repo)
    deploy_claude.install_claude(dry_run=False)
    assert "claude CLI not on PATH" in capsys.readouterr().out


def test_claude_cli_on_path_runs_plugin_steps(sandbox, empty_path, monkeypatch):
    _declare_local_self_plugin(sandbox.repo)
    fake_cli = empty_path / "claude"
    fake_cli.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_cli.chmod(0o755)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    deploy_claude.install_claude(dry_run=False)
    assert calls[0] == ["claude", "plugin", "list"]
    assert ["claude", "plugin", "install", "self@self", "--scope", "user"] in calls
