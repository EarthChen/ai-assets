---
name: code-quality-gate
description: "Pre-completion quality gate: security incident response, code quality checklist, test-type selection, review criteria and severity. Use before marking work done, before commits/reviews, or when a security issue is discovered."
---

# Quality Gate

The pre-completion gate. Apply all four sections to the current change; section 1 preempts everything else when triggered.

## 1. Security incident response (immediate)

If a security vulnerability or sensitive-data exposure is found in code, dependencies, or configuration — stop all other work:

1. STOP immediately
2. Use the **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review the entire codebase for similar issues

## 2. Code quality checklist (before marking done)

- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values (use constants or config)
- [ ] No mutation in new code (immutable patterns used)

## 3. Test types

Required where the project has the corresponding test surface:

1. **Unit Tests** — individual functions, utilities, components
2. **Integration Tests** — API endpoints, database operations
3. **E2E Tests** — critical user flows (framework chosen per language)

Troubleshooting failures: diagnose via the `/tdd` workflow → check test isolation → verify mocks are correct → fix the implementation, not the tests (unless the tests are wrong).

## 4. Review standards

**MANDATORY review triggers:**

- After writing or modifying code
- Before any commit to shared branches
- When security-sensitive code is changed (auth, payments, user data)
- When architectural changes are made
- Before merging pull requests

**Security review triggers — STOP and use security-reviewer when touching:** authentication/authorization code, user input handling, database queries, file system operations, external API calls, cryptographic operations, payment or financial code.

**Severity:**

| Level | Meaning | Action |
| ------- | --------- | -------- |
| CRITICAL | Security vulnerability or data loss risk | **BLOCK** - Must fix before merge |
| HIGH | Bug or significant quality issue | **WARN** - Should fix before merge |
| MEDIUM | Maintainability concern | **INFO** - Consider fixing |
| LOW | Style or minor suggestion | **NOTE** - Optional |

**Reviewer routing:** `/code-review` skill (dual-axis Standards + Spec review), `security-reviewer`, `typescript-reviewer`, `python-reviewer`.

**Approval:** Approve = no CRITICAL or HIGH; Warning = only HIGH issues (merge with caution); Block = CRITICAL issues found.

> Quality/security checklists live in the coding-style, security, and testing rules; the `/code-review` skill carries the detailed review workflow.

## Completion criterion

Checklist passes for the change, required test types exist, review routing decided — and the incident protocol ran if anything security-related surfaced.
