"""Shared test sandbox for the installer package.

Every test runs against a throwaway HOME and a throwaway repo root. The
installer binds HOME-derived paths at import time and also expands `~` at
call time, so both the module constants and the HOME env var are redirected.
`subprocess.run` is blocked so no test can reach the real `claude` CLI or
run git in the real repo; a test that needs a subprocess captures the real
function at its own import time.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from installer import paths


def _point_installer_at(monkeypatch: pytest.MonkeyPatch, repo: Path, home: Path) -> None:
    """Redirect every path constant the installer reads to the sandbox."""
    monkeypatch.setattr(paths, "REPO_ROOT", repo)
    monkeypatch.setattr(paths, "HOME", home)
    monkeypatch.setattr(paths, "DIST", repo / "_dist")
    monkeypatch.setattr(paths, "CLAUDE_HOME", home / ".claude")
    monkeypatch.setattr(paths, "CODEX_HOME", home / ".codex")
    monkeypatch.setattr(paths, "CURSOR_HOME", home / ".cursor")
    monkeypatch.setattr(paths, "AGENTS_HOME", home / ".agents")
    monkeypatch.setattr(paths, "PI_AGENT_HOME", home / ".pi" / "agent")
    monkeypatch.setattr(paths, "THIRD_PARTY_JSON", repo / "third-party.json")
    monkeypatch.setattr(paths, "PLUGIN_JSONS", [
        repo / ".cursor-plugin" / "plugin.json",
        repo / ".claude-plugin" / "plugin.json",
    ])
    monkeypatch.setattr(paths, "MARKETPLACE_JSON", repo / ".claude-plugin" / "marketplace.json")


@pytest.fixture(autouse=True)
def sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    home.mkdir()
    repo.mkdir()
    monkeypatch.setenv("HOME", str(home))
    _point_installer_at(monkeypatch, repo, home)

    def _blocked_run(*args, **kwargs):
        raise AssertionError(f"unexpected subprocess.run in test: {args!r}")

    monkeypatch.setattr(subprocess, "run", _blocked_run)
    return SimpleNamespace(home=home, repo=repo)


@pytest.fixture
def empty_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """PATH with no executables, so shutil.which finds no agent CLI."""
    bin_dir = tmp_path / "empty-bin"
    bin_dir.mkdir()
    monkeypatch.setenv("PATH", str(bin_dir))
    return bin_dir


def make_skill(root: Path, name: str) -> Path:
    """Create <root>/<name>/SKILL.md and return the skill dir."""
    skill = root / name
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
    return skill


def make_agent(root: Path, name: str) -> Path:
    """Create <root>/<name>.md and return the file."""
    root.mkdir(parents=True, exist_ok=True)
    agent = root / f"{name}.md"
    agent.write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
    return agent


def link(path: Path, target: Path) -> Path:
    """Create a symlink at path -> target (parents created)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)
    return path
