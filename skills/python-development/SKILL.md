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

- Tooling follows the global tech-stack rule. A new project uses uv: every tool runs through `uv run`, dependencies live in `pyproject.toml`. An existing project keeps its own dependency manager (`poetry.lock` → `poetry run`, `Pipfile.lock` → `pipenv run`, none → the commands in its README / Makefile / CI); the `uv run` commands in the references then run through that tool.
- Test-first: load the `tdd` skill; the gate is the global testing rule (every agreed seam has a test; 80% coverage is a reference); fix the implementation, not the failing test.

## Completion criterion

The project's lint, type-check, and test commands pass (uv project: `uv run ruff check .`, `uv run mypy .`, `uv run pytest --cov`), every agreed seam has a test, and the coverage figure is in your final message.
