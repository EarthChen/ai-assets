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

Troubleshooting failures: diagnose by loading the `diagnosing-bugs` skill → check test isolation → verify mocks are correct → fix the implementation, not the tests (unless the tests are wrong).

## 4. Review standards

**MANDATORY review triggers** (each is a concrete event). The review is the mattpocock `code-review` skill (Claude Code name: `mattpocock-skills:code-review`); a diff that hits the security list below also gets the `code-reviewer` agent. A diff already reviewed in this session (the same diff, or that diff plus fixes for its findings) needs no second review.

- Before a push to a shared branch: the default branch, or a release or environment branch (`release/*`, `staging`, `test`). Your own feature branch is not shared. The `ship-to-test` skill is exempt: the user invokes it, and its target is a test environment.
- Before merging a PR / MR
- Step 4 of the `feature-workflow` skill

**Security review triggers — STOP and use the `code-reviewer` agent when the diff touches any of:** authentication or authorization, cryptography, payment or financial logic, secrets or credentials handling, handling of user-supplied input (request parameters, uploads, URLs, file paths, shell arguments), SQL built from strings. Other diffs need no security dispatch.

When the diff handles requests, user input, or data access (even without a dispatch trigger), check the items that apply:

- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on public endpoints
- [ ] Error messages don't leak sensitive data

**Severity** (applies to `code-reviewer` agent / code-audit output only; the mattpocock `code-review` skill reports Standards and Spec findings without severity — address every Spec finding, fix or explicitly justify each Standards finding):

| Level | Meaning | Action |
| ------- | --------- | -------- |
| CRITICAL | Security vulnerability or data loss risk | **BLOCK** - Must fix before merge |
| HIGH | Bug or significant quality issue | **BLOCK** - Must fix before merge |
| MEDIUM | Maintainability concern | **WARN** - Consider fixing |
| LOW | Style or minor suggestion | **NOTE** - Optional |

**Reviewer routing:** the `agent-orchestration` skill's "Pick the reviewer / simplifier" table is the single route.

**Approval** (`code-reviewer` output; the single source for approval rules): Approve = no CRITICAL or HIGH; Warning = MEDIUM issues only (merge with caution); Block = CRITICAL or HIGH issues found. The code-audit language checklists use the same rule.

> The coding-style and testing rules carry further checklists.

## 5. Misses become checks

When human review catches something the gate missed, turn it into a diff-triggered checklist item: phrase the trigger so it reads from a diff, add it only after the same gap appears twice, and try to disprove it before enrolling. Prune stale items on each pass — a checklist that only grows trains ignoring.

## Completion criterion

Checklist passes for the change, required test types exist, review routing decided — and the incident protocol ran if anything security-related surfaced. A completion claim carries its evidence: the checks that ran with their results (E2E: screenshot or trace; a reported failure: the original output).
