---
name: python-development
description: "Use when writing or reviewing Python code (pytest, type hints, FastAPI, project structure), or setting up Python editor hooks."
---

# Python

Python conventions. Load only the reference matching the current task branch.

## Routing

| Task branch | Reference to read |
| --- | --- |
| Idioms, readability, EAFP, type hints, project structure, performance | `references/patterns.md` |
| pytest: TDD workflow, fixtures, mocking, parametrization, coverage | `references/testing.md` |
| FastAPI services: app factory, async discipline, DI, schemas, security, testing | `references/fastapi.md` |
| Code-level security: secrets, SQL injection, deserialisation, auth, output rendering | `references/security.md` |
| PostToolUse hooks: format-on-edit, type-check-on-edit, print() detection | `references/hooks.md` |

## Always

- EAFP over LBYL; explicit over implicit.
- Type hints on public functions.
- Test-first via the `tdd` skill; coverage target is the global 80% testing rule; fix the implementation, not the failing test.

## Completion criterion

Every module touched by the task was checked against the matching branch reference, and the test suite is green with coverage at target.
