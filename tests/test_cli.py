"""CLI: platform detection, explicit-platform guard, version subcommand."""

from __future__ import annotations

import json
import sys

import pytest

from installer import cli, version


def test_detect_platforms_falls_back_to_config_dirs(sandbox, empty_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")  # skip the macOS app-bundle probe
    (sandbox.home / ".claude").mkdir()
    (sandbox.home / ".pi" / "agent").mkdir(parents=True)

    detected = cli.detect_platforms(home=sandbox.home)

    assert {name: ok for name, (ok, _) in detected.items()} == {
        "claude": True, "codex": False, "cursor": False, "pi": True}
    assert detected["claude"][1].startswith("config dir:")


def test_detect_platforms_prefers_cli_on_path(sandbox, empty_path):
    fake = empty_path / "codex"
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    fake.chmod(0o755)
    assert cli.detect_platforms(home=sandbox.home)["codex"] == (
        True, f"codex CLI on PATH: {fake}")


def test_explicit_platform_that_is_not_detected_fails_loud(sandbox, empty_path, monkeypatch):
    # An explicit --platform for a missing tool is a typo or an install gap;
    # writing its config anyway would go unnoticed.
    monkeypatch.setattr(sys, "platform", "linux")
    vendor = sandbox.repo / "vendor" / "mattpocock-skills"
    vendor.mkdir(parents=True)
    (vendor / ".placeholder").write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="platform 'codex' not detected"):
        cli._do_install("codex", dry_run=False)
    assert not (sandbox.home / ".codex").exists()


def _write_manifests(repo, ver):
    for d in (".cursor-plugin", ".claude-plugin"):
        (repo / d).mkdir(exist_ok=True)
        (repo / d / "plugin.json").write_text(json.dumps({"version": ver}), encoding="utf-8")
    (repo / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
        {"plugins": [{"name": "earthchen-ai-assets", "version": ver}]}), encoding="utf-8")


def test_version_bump_updates_every_manifest_and_marketplace(sandbox, monkeypatch):
    repo = sandbox.repo
    _write_manifests(repo, "1.3.2")
    monkeypatch.setattr(sys, "argv", ["install.py", "version", "--bump", "minor"])

    cli.main()

    for d in (".cursor-plugin", ".claude-plugin"):
        assert json.loads((repo / d / "plugin.json").read_text())["version"] == "1.4.0"
    market = json.loads((repo / ".claude-plugin" / "marketplace.json").read_text())
    assert market["plugins"][0]["version"] == "1.4.0"


def test_version_dry_run_changes_nothing(sandbox):
    _write_manifests(sandbox.repo, "1.3.2")
    version.set_version("9.9.9", dry_run=True)
    assert version._get_current_version() == "1.3.2"


def test_version_without_args_prints_current(sandbox, monkeypatch, capsys):
    _write_manifests(sandbox.repo, "1.3.2")
    monkeypatch.setattr(sys, "argv", ["install.py", "version"])
    cli.main()
    assert "Current version: 1.3.2" in capsys.readouterr().out
