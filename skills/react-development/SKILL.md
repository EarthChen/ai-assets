---
name: react-development
description: React/TSX development conventions — coding style, component architecture patterns, security, RTL testing. Use when writing or reviewing React/TSX components or hooks.
---

# React

React/TSX conventions. Load only the reference matching the current task branch.

## Routing

| Task branch | Reference to read |
| --- | --- |
| Naming, file extensions/layout, JSX, imports, hooks discipline, state shape | `references/coding-style.md` |
| Component architecture: container/presentational, state location, RSC boundary, Suspense, forms, data fetching, composition | `references/patterns.md` |
| User input, `dangerouslySetInnerHTML`, links and `target=_blank`, Server Actions, secrets, CSP | `references/security.md` |
| Writing or reviewing tests: RTL queries, userEvent, async assertions, MSW, accessibility | `references/testing.md` |

## Always

- Server Components by default; add `'use client'` only for interactivity.
- React Testing Library for component tests; prefer `getByRole` queries.
- Validate all Server Action input; sanitize everything reaching `dangerouslySetInnerHTML`.
- Function components and hooks; class components only when touching legacy code.

## Completion criterion

Every file touched by the task was checked against the matching branch reference, and all "Always" rules hold.
