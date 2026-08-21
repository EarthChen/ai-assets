---
name: typescript-development
description: "TypeScript/Node backend development conventions — testing conventions (vitest/jest, supertest, testcontainers-node), mock boundaries. Use when writing or reviewing TypeScript backend code."
---

# TypeScript Backend

Conventions for Node/TypeScript backend services. Minimal by design: branches are added as they earn their place.

## Routing

| Task branch | Reference to read |
| --- | --- |
| Unit + integration testing: vitest/jest, supertest, testcontainers-node, mock boundaries, test isolation | `references/integration-testing.md` |

## Always

- Testing principles (boundaries, sociable/solitary, narrow integration, isolation rules) live once in `~/.agents/skills/testing-principles/SKILL.md`; this skill carries only TypeScript specifics.
- Every endpoint has at least one integration test asserting the persisted side effect — a status code alone proves nothing.

## Completion criterion

Every new service method has unit coverage; every endpoint's integration test asserts persistence, not just the response.
