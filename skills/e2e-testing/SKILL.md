---
name: e2e-testing
disable-model-invocation: true
description: "E2E testing patterns — web frontends (Playwright: Page Object Model, configuration, CI/CD integration, artifact management, flaky test strategies) and backend APIs (three-layer assertions, auth fixtures, data isolation, schema validation)."
---

# E2E Testing Patterns

Two branches — load only what the current task touches:

- **Web frontend** (Playwright): `references/web-playwright.md` — file layout, Page Object Model, test structure, configuration, flaky-test strategies. For screenshots/traces/video, GitHub Actions CI, or the test report template: `references/web-artifacts-ci.md`
- **Backend/API**: `references/backend-api.md` — three-layer assertions, auth fixtures, data isolation, schema validation, per-stack examples (pytest + httpx, supertest, REST Assured)
