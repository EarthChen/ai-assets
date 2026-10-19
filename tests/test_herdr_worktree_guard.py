"""PreToolUse guard: inside Herdr, worktrees come from `herdr worktree create`."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "claude" / "hooks" / "herdr_worktree_guard.py"
# conftest blocks subprocess.run per test; bind the real one at import time.
_REAL_RUN = subprocess.run


def _run(payload, *, herdr: bool, raw: str | None = None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_")}
    if herdr:
        env["HERDR_ENV"] = "1"
    return _REAL_RUN(
        [sys.executable, "-I", str(SCRIPT)],
        input=raw if raw is not None else json.dumps(payload),
        capture_output=True, text=True, env=env,
    )


def _bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def _decision(result) -> str | None:
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize("command", [
    "git worktree add ../x -b feat/x",
    "git -C /repo worktree add ../x",
    "cd /repo && git worktree add ../x main",
    "git fetch origin; git --no-pager worktree add ../x",
])
def test_git_worktree_add_is_denied_inside_herdr(command):
    # Herdr tracks worktrees as workspaces; a raw `git worktree add` is invisible to it.
    result = _run(_bash(command), herdr=True)

    assert result.returncode == 0
    assert _decision(result) == "deny"
    reason = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "herdr worktree create" in reason


@pytest.mark.parametrize("tool_input", [{}, {"name": "probe"}])
def test_enter_worktree_creation_is_denied_inside_herdr(tool_input):
    # The built-in tool creates a git worktree without going through Bash.
    result = _run({"tool_name": "EnterWorktree", "tool_input": tool_input}, herdr=True)

    assert _decision(result) == "deny"


def test_enter_worktree_into_an_existing_path_passes_inside_herdr():
    # `path` only switches into a worktree that exists, such as one just made
    # by `herdr worktree create`. Denying it would block the sanctioned flow.
    result = _run({"tool_name": "EnterWorktree", "tool_input": {"path": "/repo-wt"}}, herdr=True)

    assert _decision(result) is None


@pytest.mark.parametrize("command", [
    "herdr worktree create --branch feat/x",
    "git worktree list",
    "git worktree remove ../x",
    "git status",
    "ls",
])
def test_other_commands_pass_inside_herdr(command):
    result = _run(_bash(command), herdr=True)

    assert result.returncode == 0
    assert _decision(result) is None


def test_everything_passes_outside_herdr():
    assert _decision(_run(_bash("git worktree add ../x"), herdr=False)) is None
    assert _decision(_run({"tool_name": "EnterWorktree", "tool_input": {}}, herdr=False)) is None


def test_malformed_input_fails_open_with_a_message():
    # A broken payload must not block every Bash call, but must not vanish silently.
    result = _run(None, herdr=True, raw="not json")

    assert result.returncode == 0
    assert _decision(result) is None
    assert "herdr_worktree_guard" in result.stderr
