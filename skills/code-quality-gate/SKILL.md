---
name: code-quality-gate
description: "Use before marking work done or when a security issue is discovered: security incident response, quality checklist, test-type selection, review severity."
---

# Quality Gate

The pre-completion gate. Apply all four sections to the current change; section 1 preempts everything else when triggered.

## 1. Security incident response (immediate)

If a security vulnerability or sensitive-data exposure is found in code, dependencies, or configuration — stop all other work:

1. STOP immediately
2. Use the **`code-reviewer`** agent (its security lens)
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review the entire codebase for similar issues

## 2. Code quality checklist (before marking done)

- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] No deep nesting (>4 levels)
- [ ] No hardcoded values (use constants or config)

## 3. Test types

Required where the project has the corresponding test surface:

1. **Unit Tests** — individual functions, utilities, components
2. **Integration Tests** — API endpoints, database operations
3. **E2E Tests** — critical user flows (framework chosen per language)

Troubleshooting failures: diagnose by calling the Skill tool with "diagnosing-bugs" → check test isolation → verify mocks are correct → fix the implementation, not the tests (unless the tests are wrong).

## 4. Review standards

**MANDATORY review triggers:**

- After writing or modifying code
- Before any commit to shared branches
- When security-sensitive code is changed (auth, payments, user data)
- When architectural changes are made
- Before merging pull requests

**Security review triggers — STOP and use the `code-reviewer` agent when touching:** authentication/authorization code, user input handling, database queries, file system operations, external API calls, cryptographic operations, payment or financial code. The security checks themselves live in the security rule.

**Severity** (applies to `code-reviewer` agent / code-audit output only; the mattpocock `code-review` skill reports Standards and Spec findings without severity — address every Spec finding, fix or explicitly justify each Standards finding):

| Level | Meaning | Action |
| ------- | --------- | -------- |
| CRITICAL | Security vulnerability or data loss risk | **BLOCK** - Must fix before merge |
| HIGH | Bug or significant quality issue | **BLOCK** - Must fix before merge |
| MEDIUM | Maintainability concern | **WARN** - Consider fixing |
| LOW | Style or minor suggestion | **NOTE** - Optional |

**Reviewer routing:** the `agent-orchestration` skill's "Pick the reviewer / simplifier" table is the single route.

**Approval** (`code-reviewer` output; the single source for approval rules): Approve = no CRITICAL or HIGH; Warning = MEDIUM issues only (merge with caution); Block = CRITICAL or HIGH issues found. The code-audit language checklists use the same rule.

> Quality/security checklists live in the coding-style, security, and testing rules.

## Completion criterion

Checklist passes for the change, required test types exist, review routing decided — and the incident protocol ran if anything security-related surfaced.
