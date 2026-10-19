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
import sys

# ceiling: a regex over the raw command string. It also matches `git worktree
# add` inside quotes (an echo, a commit message). Upgrade path: shlex-split
# each command segment and compare argv.
_GIT_WORKTREE_ADD = re.compile(r"\bgit\b(?:\s+-\S+(?:\s+\S+)?)*\s+worktree\s+add\b")

_REASON = (
    "This session runs inside Herdr (HERDR_ENV=1). Create the worktree with "
    "`herdr worktree create --branch <name> --base <ref>` (load the `herdr` skill; "
    "see `herdr worktree create --help`). Herdr opens it as a workspace."
)


def _creates_worktree(payload: dict) -> bool:
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if tool == "EnterWorktree":
        # `path` switches into an existing worktree; only `name` or nothing creates one.
        return not tool_input.get("path")
    if tool == "Bash":
        return bool(_GIT_WORKTREE_ADD.search(tool_input.get("command") or ""))
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
