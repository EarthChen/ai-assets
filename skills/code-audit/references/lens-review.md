# Lens Review

Cross-language review lenses — silent failure hunting, type design analysis, and security vulnerability detection. These are pattern-level checks ("is this error silently swallowed?", "do these types make illegal states impossible?", "is this an OWASP Top 10 issue?"), orthogonal to the language-specific rules in `references/<lang>-review.md` which cover language-specific rules ("is this Java catch block written correctly?"). Loaded by `skills/code-audit/rules.md` when the lens axis runs.

## Silent Failure Hunting

## Hunt Targets

### 1. Empty Catch Blocks

- `catch {}` or ignored exceptions
- errors converted to `null` / empty arrays with no context

### 2. Inadequate Logging

- logs without enough context
- wrong severity
- log-and-forget handling

### 3. Dangerous Fallbacks

- default values that hide real failure
- `.catch(() => [])`
- graceful-looking paths that make downstream bugs harder to diagnose

### 4. Error Propagation Issues

- lost stack traces
- generic rethrows
- missing async handling

### 5. Missing Error Handling

- no timeout or error handling around network/file/db paths
- no rollback around transactional work

## Type Design Analysis

## Evaluation Criteria

### 1. Encapsulation

- are internal details hidden
- can invariants be violated from outside

### 2. Invariant Expression

- do the types encode business rules
- are impossible states prevented at the type level

### 3. Invariant Usefulness

- do these invariants prevent real bugs
- are they aligned with the domain

### 4. Enforcement

- are invariants enforced by the type system
- are there easy escape hatches

## Security Review

## Step 1: Detect the Language and Dependency-Audit Tool

Run these probes to identify the project's language, then run the matching audit command:

```bash
# Detect
cat package.json 2>/dev/null | head -20
cat pyproject.toml 2>/dev/null || cat requirements.txt 2>/dev/null
cat go.mod 2>/dev/null
cat Cargo.toml 2>/dev/null
cat pom.xml 2>/dev/null | head -20 || cat build.gradle 2>/dev/null | head -20
```

| Language | Dependency audit command | Static security linter |
| --- | --- | --- |
| TypeScript / JavaScript | `pnpm audit --audit-level high` (or `yarn audit` when the lockfile says so) | `pnpm exec eslint . --plugin security` |
| Python | `uv run pip-audit` or `pip-audit` / `safety scan` | `ruff check --select S` (bandit also valid) |
| Go | `govulncheck ./...` | `gosec ./...` |
| Rust | `cargo audit` | `cargo audit` |
| Java (Maven) | `./mvnw org.owasp:dependency-check:check` | SpotBugs with find-sec-bugs |
| Java (Gradle) | `./gradlew dependencyCheckAnalyze` | SpotBugs with find-sec-bugs |

Run the matching audit + linter. If neither is configured, note it as a finding (no automated dependency CVE check).

## Review Workflow

### 1. Initial Scan

- Run the matched dependency-audit + security linter, search for hardcoded secrets
- Review high-risk areas: auth, API endpoints, DB queries, file uploads, payments, webhooks, deserialization, shell exec

### 2. OWASP Top 10 Check

1. **Injection** — Queries parameterized? User input sanitized? ORMs used safely? (SQL/NoSQL/command injection)
2. **Broken Auth** — Passwords hashed (bcrypt/argon2 or language equivalent)? JWT validated? Sessions secure?
3. **Sensitive Data** — HTTPS enforced? Secrets in env vars? PII encrypted? Logs sanitized?
4. **XXE** — XML parsers configured securely? External entities disabled?
5. **Broken Access** — Auth checked on every route? CORS properly configured?
6. **Misconfiguration** — Default creds changed? Debug mode off in prod? Security headers set?
7. **XSS** — Output escaped? CSP set? Framework auto-escaping? (applies to any HTML-rendering backend, not just JS)
8. **Insecure Deserialization** — User input deserialized safely? (pickle, eval, ObjectInputStream, unsafe YAML load, etc.)
9. **Known Vulnerabilities** — Dependencies up to date? Dependency audit clean? (use the language-matched tool from Step 1)
10. **Insufficient Logging** — Security events logged? Alerts configured?

### 3. Code Pattern Review

Flag these patterns immediately (language-agnostic — map to the equivalent in the project's language):

| Pattern | Severity | Fix |
| --- | --- | --- |
| Hardcoded secrets | CRITICAL | Use env vars / secret manager |
| Shell command with user input | CRITICAL | Use safe APIs (execFile, subprocess with list args, never shell=True) |
| String-concatenated SQL | CRITICAL | Parameterized queries / prepared statements |
| Unescaped user input rendered to HTML | HIGH | Escape output / use framework auto-escaping / sanitize |
| `fetch(userProvidedUrl)` / SSRF | HIGH | Whitelist allowed domains |
| Plaintext password comparison | CRITICAL | Use constant-time compare / `bcrypt.compare()` or equivalent |
| No auth check on route | CRITICAL | Add authentication middleware |
| Balance check without lock | CRITICAL | Use row lock / `SELECT ... FOR UPDATE` in transaction |
| No rate limiting on auth/sensitive endpoints | HIGH | Add rate limiting (language-appropriate middleware) |
| Logging passwords/secrets | MEDIUM | Sanitize log output |
| Unsafe deserialization of user input | CRITICAL | Use safe serializers / allowlist classes |

## Common False Positives

- Environment variables in `.env.example` (not actual secrets)
- Test credentials in test files (if clearly marked)
- Public API keys (if actually meant to be public)
- SHA256/MD5 used for checksums (not passwords)

**Always verify context before flagging.**
