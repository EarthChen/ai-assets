---
name: python-development
description: Python development conventions — idioms, type hints, project structure, pytest testing with TDD, FastAPI services, code-level security, editor hooks. Use when writing or reviewing Python code.
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
- Red-green-refactor via the `tdd` skill; fix the implementation, not the failing test.

## Completion criterion

Every module touched by the task was checked against the matching branch reference, and the test suite is green with coverage at target.
