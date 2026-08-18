---
name: python
description: Python development conventions — idioms, type hints, project structure, pytest testing with TDD. Use when writing or reviewing Python code.
---

# Python

Python conventions. Load only the reference matching the current task branch.

## Routing

| Task branch | Reference to read |
| --- | --- |
| Idioms, readability, EAFP, type hints, project structure, performance | `references/patterns.md` |
| pytest: TDD workflow, fixtures, mocking, parametrization, coverage | `references/testing.md` |

## Always

- EAFP over LBYL; explicit over implicit.
- Type hints on public functions.
- Red-green-refactor via the `/tdd` skill; fix the implementation, not the failing test.

## Completion criterion

Every module touched by the task was checked against the matching branch reference, and the test suite is green with coverage at target.
