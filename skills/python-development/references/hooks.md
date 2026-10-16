# Python Hooks

PostToolUse hook recipes for `~/.claude/settings.json` (user level) or `.claude/settings.json` (project level). The commands call `uv run`, so use project level for uv projects and keep tool versions pinned by `pyproject.toml`.

## Contract

A PostToolUse hook receives the tool call as **JSON on stdin**, never as argv. `tool_input.file_path` names the file just written. Filter to `.py` and scope every command to that one file; otherwise the hook acts on non-Python files or re-checks the whole project on each edit.

## Recipes

### Format on Edit

One formatter per project (`ruff format`, or `black`).

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path // empty' | grep -E '\\.py$' | xargs -r uv run ruff format --"
          }
        ]
      }
    ]
  }
}
```

### Type-Check on Edit

One checker per project (`mypy`, or `pyright`). Same filter, different tail:

```json
"command": "jq -r '.tool_input.file_path // empty' | grep -E '\\.py$' | xargs -r uv run mypy --no-incremental"
```

### Print Statement Detection

Warn when `print()` survives in a non-test file; `logging` replaces it.

```python
# scripts/check_no_print.py
"""Report print() in the file a PostToolUse hook just edited."""
import json
import re
import sys

PRINT_RE = re.compile(r"^\s*print\(", re.M)
TEST_PATH = re.compile(r"test_|/tests/|conftest\.py")

payload = json.load(sys.stdin)
path = payload.get("tool_input", {}).get("file_path", "")
if not path.endswith(".py") or TEST_PATH.search(path):
    sys.exit(0)

with open(path, encoding="utf-8") as f:
    if PRINT_RE.search(f.read()):
        print(f"{path}: print() found — use logging instead", file=sys.stderr)
        sys.exit(2)  # exit 2 feeds stderr back to the agent so it can fix the file
```

Hook command (quote the variable; `$CLAUDE_PROJECT_DIR` is the project root):

```json
"command": "uv run python \"$CLAUDE_PROJECT_DIR\"/scripts/check_no_print.py"
```
