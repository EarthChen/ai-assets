#!/usr/bin/env python3
"""PreToolUse guard: inside Herdr, deny raw git worktree creation.

Herdr tracks worktrees as workspaces, so worktrees must come from
`herdr worktree create`. Reads the hook payload on stdin; prints a deny
decision to stdout. Fails open on a malformed payload, with a stderr message.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

_REASON = (
    "This session runs inside Herdr (HERDR_ENV=1). Create the worktree with "
    "`herdr worktree create --branch <name> --base <ref>` (load the `herdr` skill; "
    "see `herdr worktree create --help`). Herdr opens it as a workspace."
)

_SHELLS = {"bash", "sh", "zsh", "dash"}
_WRAPPERS = {"sudo", "env", "command", "builtin", "exec", "time", "nohup", "nice"}
# git global options that take their value as the next token.
_GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z0-9_]+)\1")
_SEPARATORS = {";", "&", "&&", "|", "||", "(", ")", "\n", "|&"}


def _strip_heredocs(command: str) -> str:
    """Drop heredoc bodies: they are data for a command, not commands."""
    kept: list[str] = []
    delimiter: str | None = None
    for line in command.split("\n"):
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        kept.append(line)
        match = _HEREDOC.search(line)
        if match:
            delimiter = match.group(2)
    return "\n".join(kept)


def _segments(command: str) -> list[list[str]]:
    """Split a command line into argv lists at unquoted shell separators."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = "#"
    segments: list[list[str]] = [[]]
    for token in lexer:
        if token and set(token) <= set(";&|()\n"):
            if segments[-1]:
                segments.append([])
        else:
            segments[-1].append(token)
    return [seg for seg in segments if seg]


def _leading_command(argv: list[str]) -> list[str]:
    """Skip env assignments and wrappers (sudo, env, ...) before the real command."""
    i = 0
    while i < len(argv):
        token = argv[i]
        if _ASSIGNMENT.match(token) or token in _WRAPPERS or (token.startswith("-") and i > 0):
            i += 1
        else:
            break
    return argv[i:]


def _is_git_worktree_add(argv: list[str]) -> bool:
    if not argv or os.path.basename(argv[0]) != "git":
        return False
    i = 1
    while i < len(argv) and argv[i].startswith("-"):
        i += 2 if argv[i] in _GIT_VALUE_OPTIONS else 1
    return argv[i : i + 2] == ["worktree", "add"]


# ceiling: command substitution inside double quotes ("$(git worktree add)")
# and xargs-style indirection stay invisible to the parser. Upgrade path: a
# real shell parser (bashlex) instead of shlex tokens.
def _runs_worktree_add(command: str) -> bool:
    try:
        segments = _segments(_strip_heredocs(command))
    except ValueError:
        # Unbalanced quotes: the shell rejects the command, so nothing runs.
        return False
    for segment in segments:
        argv = _leading_command(segment)
        if _is_git_worktree_add(argv):
            return True
        if argv and os.path.basename(argv[0]) in _SHELLS:
            # `bash -c '<script>'` runs the script string as commands.
            for flag, script in zip(argv[1:], argv[2:]):
                if flag.startswith("-") and "c" in flag and _runs_worktree_add(script):
                    return True
    return False


def _creates_worktree(payload: dict) -> bool:
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if tool == "EnterWorktree":
        # `path` switches into an existing worktree; only `name` or nothing creates one.
        return not tool_input.get("path")
    if tool == "Bash":
        return _runs_worktree_add(tool_input.get("command") or "")
    return False


def main() -> int:
    if os.environ.get("HERDR_ENV") != "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"herdr_worktree_guard: unreadable hook payload, allowing: {exc}", file=sys.stderr)
        return 0
    if not isinstance(payload, dict) or not _creates_worktree(payload):
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": _REASON,
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
