---
name: testing-standards
description: Use when deciding which test types to write (unit, integration, E2E) or troubleshooting failing test suites — isolation, mocks, fix-implementation
---

# Testing Standards — Test Types & Failure Troubleshooting

## When to Use

Use this skill when determining the required test types for a feature (unit, integration, E2E) or when tests fail and you need to diagnose via the `/tdd` workflow, check test isolation, or verify that mocks are correct.

## Test Types

Test Types (required where the project has the corresponding test surface):

1. **Unit Tests** - Individual functions, utilities, components
2. **Integration Tests** - API endpoints, database operations
3. **E2E Tests** - Critical user flows (framework chosen per language)

## Troubleshooting Test Failures

1. Use the `/tdd` skill (mattpocock/skills workflow)
2. Check test isolation
3. Verify mocks are correct
4. Fix implementation, not tests (unless tests are wrong)
