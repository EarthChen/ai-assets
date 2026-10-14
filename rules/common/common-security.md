---
description: "Security: mandatory checks, secret management"
alwaysApply: true
---
# Security Guidelines

## Mandatory Security Checks

Before ANY commit:

- [ ] No hardcoded secrets (API keys, passwords, tokens)

Before committing code that handles requests, user input, or data access, check the items that apply:

- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on public endpoints
- [ ] Error messages don't leak sensitive data

## Secret Management

- ALWAYS use environment variables or a secret manager
- Validate that required secrets are present at startup
- Rotate any secrets that may have been exposed
