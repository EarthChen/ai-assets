# Java Security

Java-specific security gotchas. Generic rules (no hardcoded secrets, parameterised SQL, input validation, safe error messages) come from the global security rule; this file adds what Java and Spring change.

## Gotchas

- Native queries: bind every value as a parameter (`:param`, `?`). Identifiers (table, column, sort field) cannot be bound; validate them against an allowlist.
- Authorization: enforce at the service boundary, not only in controllers.
- Passwords: use Spring Security's `PasswordEncoder` (bcrypt or Argon2). Use an established library (Spring Security, jjwt) for tokens.
- Error responses: map exceptions at the handler boundary to generic messages; log details server-side. `ex.getMessage()` and `SQLException` text leak schema and paths.
- Logs: omit full request bodies, passwords, tokens, session IDs, PII.
- Redirect URLs from user input: validate against an allowlist.
- Secrets: bind from environment through `@ConfigurationProperties` (Spring) or `@ConfigMapping` (Quarkus); fail at startup when missing.

## Scanners

- Dependencies: OWASP Dependency-Check plugin (run in `verification.md` Phase 5); Renovate or Dependabot for updates
- Static analysis: SpotBugs needs the OWASP **find-sec-bugs** plugin (SpotBugs has no built-in security ruleset)
