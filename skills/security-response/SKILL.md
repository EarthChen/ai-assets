---
name: security-response
description: Use when a security issue or sensitive-data exposure is discovered — STOP, route to security-reviewer, fix CRITICAL, rotate secrets, audit the codebase
---

# Security Response Protocol

## When to Use

Use this skill immediately when a security vulnerability or sensitive-data exposure is found in code, dependencies, or configuration — before any further work proceeds. This is the incident-response escalation path triggered by the security review.

## Security Response Protocol

If security issue found:

1. STOP immediately
2. Use **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
