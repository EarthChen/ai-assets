# Security Guidelines

## Mandatory Security Checks

Before ANY commit:

- [ ] No hardcoded secrets (API keys, passwords, tokens)

Before committing code that handles requests, user input, or data access, run the security checklist in the `code-quality-gate` skill (Review standards) and check the items that apply.

## Secret Management

- ALWAYS use environment variables or a secret manager
- Validate that required secrets are present at startup
- Rotate any secrets that may have been exposed
