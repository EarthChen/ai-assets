---
description: "Testing requirements: 80% coverage, TDD workflow, test types"
alwaysApply: true
---
# Testing Requirements

## Minimum Test Coverage: 80%

Test Types (required where the project has the corresponding test surface):
1. **Unit Tests** - Individual functions, utilities, components
2. **Integration Tests** - API endpoints, database operations
3. **E2E Tests** - Critical user flows (framework chosen per language)

## Test-Driven Development

TDD is mandatory for new features and bug fixes — the red-green-refactor loop is carried by the `/tdd` skill (see the development workflow rule).

## Troubleshooting Test Failures

1. Use the `/tdd` skill (mattpocock/skills workflow)
2. Check test isolation
3. Verify mocks are correct
4. Fix implementation, not tests (unless tests are wrong)

## Skill Support

- `/tdd` (mattpocock/skills) - Red-green-refactor loop with seam-based testing; use for new features and bug fixes
