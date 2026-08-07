---
name: code-review-standards
description: "Code review standards: when to review, severity levels, security triggers, agent/skill routing, approval criteria. Use after writing/modifying code, before commits/merges, or for security-sensitive changes."
---

# Code Review Standards

## When to Use

- After writing or modifying code, before commits to shared branches, before merging PRs, or when architectural/security-sensitive code changes.
- You need to classify an issue's severity (CRITICAL / HIGH / MEDIUM / LOW) or decide approval (Approve / Warning / Block).
- You need to pick the right reviewer agent or skill (`/code-review`, `security-reviewer`, `typescript-reviewer`, `python-reviewer`).

## Purpose

Code review ensures quality, security, and maintainability before code is merged. This rule defines when and how to conduct code reviews.

## When to Review

**MANDATORY review triggers:**

- After writing or modifying code
- Before any commit to shared branches
- When security-sensitive code is changed (auth, payments, user data)
- When architectural changes are made
- Before merging pull requests

> Quality/security checklists live in the coding-style, security, and testing rules; the `/code-review` skill carries the detailed review workflow.

## Security Review Triggers

**STOP and use security-reviewer agent when:**

- Authentication or authorization code
- User input handling
- Database queries
- File system operations
- External API calls
- Cryptographic operations
- Payment or financial code

## Review Severity Levels

| Level | Meaning | Action |
| ------- | --------- | -------- |
| CRITICAL | Security vulnerability or data loss risk | **BLOCK** - Must fix before merge |
| HIGH | Bug or significant quality issue | **WARN** - Should fix before merge |
| MEDIUM | Maintainability concern | **INFO** - Consider fixing |
| LOW | Style or minor suggestion | **NOTE** - Optional |

## Agent Usage

Use these agents for code review:

| Agent / Skill | Purpose |
| ------- | --------- |
| **/code-review** skill (mattpocock/skills) | General code quality, dual-axis Standards + Spec review |
| **security-reviewer** | Security vulnerabilities, OWASP Top 10 |
| **typescript-reviewer** | TypeScript/JavaScript specific issues |
| **python-reviewer** | Python specific issues |

## Approval Criteria

- **Approve**: No CRITICAL or HIGH issues
- **Warning**: Only HIGH issues (merge with caution)
- **Block**: CRITICAL issues found
