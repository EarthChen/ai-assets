---
name: python-development
description: "Use when writing or reviewing Python code (pytest, type hints, FastAPI, security, project structure), or setting up Python editor hooks."
---

# Python

Python conventions. Load only the reference matching the current task branch.

## Routing

| Task branch | Reference to read |
| --- | --- |
| Type hints, project layout, uv tooling commands, pyproject baseline | `references/patterns.md` |
| pytest: coverage, async tests, mocking, integration tests with real DB | `references/testing.md` |
| FastAPI services: app factory, async discipline, DI, schemas, security, testing | `references/fastapi.md` |
| Code-level security: secrets, SQL injection, deserialisation, auth, output rendering | `references/security.md` |
| PostToolUse hooks: format-on-edit, type-check-on-edit, print() detection | `references/hooks.md` |

## Always

- Run every tool through `uv run`; dependencies live in `pyproject.toml`.
- Test-first: call the Skill tool with "tdd"; coverage target is the global 80% testing rule; fix the implementation, not the failing test.

## Completion criterion

`uv run ruff check .`, `uv run mypy .`, and `uv run pytest --cov` all pass, and coverage meets the 80% target.
