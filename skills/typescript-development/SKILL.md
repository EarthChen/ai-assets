---
name: typescript-development
description: "Use when writing or reviewing TypeScript/Node backend code or its tests (vitest/jest, supertest, testcontainers-node)."
---

# TypeScript Backend

Conventions for Node/TypeScript backend services.

Testing: Read `references/integration-testing.md` (vitest/jest, supertest, testcontainers-node).

## Always

- Testing principles (boundaries, sociable/solitary, narrow integration, isolation rules) live once in `../testing-principles/SKILL.md` (Read it); this skill carries only TypeScript specifics.
- Test-first: call the Skill tool with "tdd".
- Every endpoint has at least one integration test asserting the persisted side effect — a status code alone proves nothing.

## Completion criterion

Every new service method has unit coverage.
