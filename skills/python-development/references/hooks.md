# Python Hooks

PostToolUse hook configuration for auto-formatting and type-checking Python files. This file carries what to write in `~/.claude/settings.json` (or the platform equivalent) — not what's already enforced by your editor's LSP.

## When to Use

- Setting up a new Python project for AI-assisted editing
- Adding format-on-save or type-check-on-save automation
- Detecting `print()` statements before they reach review

## Hard Constraints

A PostToolUse hook receives the tool call as **JSON on stdin**, never as argv. `tool_input.file_path` names the file just written — scope every command below to that one file, or the hook rewrites and re-checks the whole project on each edit.

### Format on Edit

Auto-format `.py` files after every edit. Pick one formatter per project; don't run `black` and `ruff format` simultaneously.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path // empty' | xargs -r uv run ruff format --"
          }
        ]
      }
    ]
  }
}
```

For projects on `black`:

```json
"command": "jq -r '.tool_input.file_path // empty' | xargs -r uv run black --quiet --"
```

### Type-Check on Edit

Run a type-checker after `.py` writes to surface type errors immediately. Pick `mypy` or `pyright`, not both.

```json
{
  "type": "command",
  "command": "jq -r '.tool_input.file_path // empty' | xargs -r uv run mypy --no-incremental"
}
```

For `pyright`:

```json
"command": "jq -r '.tool_input.file_path // empty' | xargs -r uv run pyright"
```

### Print Statement Detection

Warn when `print()` survives in a non-test file — use `logging` module instead. Read the path from the same stdin payload:

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
if not path or TEST_PATH.search(path):
    sys.exit(0)

if PRINT_RE.search(open(path).read()):
    print(f"{path}: print() found — use logging instead", file=sys.stderr)
    sys.exit(2)  # exit 2 feeds stderr back to the agent so it can fix the file
```

Hook command:

```json
"command": "uv run python scripts/check_no_print.py"
```

## Project-Local Configuration

The hooks above go in user-level `~/.claude/settings.json` to apply globally. For project-scoped hooks, drop the same JSON into `.claude/settings.json` at the repo root.

`uv run` resolves dependencies from the project's `pyproject.toml`, so the formatter and type-checker versions stay pinned per project.

## Anti-Patterns

- Running `black` and `ruff format` together — they produce different layouts
- Running `mypy` and `pyright` on the same edit — two type-checker outputs slow iteration
- Hooks that scan the whole project instead of the edited file — they fail on pre-existing findings and block unrelated edits
- Hooks that depend on global pip installs — use `uv run` to pin to project deps
