# Java Security

Code-level security constraints for Java services. Pair with the verification loop in `verification.md` (which runs the scanners); this file carries only what to write and what to forbid.

## When to Use

- Writing or reviewing any Java code that handles user input, secrets, persistence, auth, or external calls
- Mapping exceptions to API responses
- Wiring dependency scanning into CI
- Reviewing secrets management and credential handling

## Hard Constraints

### Secrets

- Never hardcode API keys, tokens, database URLs with credentials, or passwords in source
- Read secrets at runtime via `System.getenv("...")`; fail fast if missing
- Local config files with secrets belong in `.gitignore`; production secrets in a secret manager (Vault, AWS Secrets Manager)

```java
// BAD
private static final String API_KEY = "sk-abc123...";

// GOOD — fail fast on missing env var
String apiKey = System.getenv("PAYMENT_API_KEY");
Objects.requireNonNull(apiKey, "PAYMENT_API_KEY must be set");
```

### SQL Injection

- Parameterised queries only — no string concatenation of user input into SQL
- Use `PreparedStatement` or the framework's parameterised API (Spring `JdbcTemplate`, JPA `@Query` with `:param`)
- For native queries, validate and sanitise every interpolated parameter

```java
// BAD — string concatenation
Statement stmt = conn.createStatement();
String sql = "SELECT * FROM orders WHERE name = '" + name + "'";
stmt.executeQuery(sql);

// GOOD — PreparedStatement
PreparedStatement ps = conn.prepareStatement("SELECT * FROM orders WHERE name = ?");
ps.setString(1, name);

// GOOD — JDBC template
jdbcTemplate.query("SELECT * FROM orders WHERE name = ?", mapper, name);
```

### Input Validation

- Validate every input at the system boundary (controller, message handler, scheduled job input) before processing
- Use Bean Validation (`@NotNull`, `@NotBlank`, `@Size`) on request DTOs when the framework supports it
- For plain Java, validate manually and throw `IllegalArgumentException` with a clear message
- Sanitise file paths and user-provided strings before filesystem access

```java
public Order createOrder(String customerName, BigDecimal amount) {
    if (customerName == null || customerName.isBlank()) {
        throw new IllegalArgumentException("Customer name is required");
    }
    if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
        throw new IllegalArgumentException("Amount must be positive");
    }
    return new Order(customerName, amount);
}
```

### Authentication and Authorization

- Never implement custom password hashing or token crypto — use established libraries (Spring Security, jjwt)
- Store passwords with bcrypt or Argon2; never MD5/SHA1
- Enforce authorization checks at service boundaries, not only in controllers
- Strip sensitive data from logs: no passwords, tokens, session IDs, PII, full request bodies with credentials

### Error Messages

- Never expose stack traces, internal paths, SQL fragments, or `ex.getMessage()` in API responses
- Map exceptions to safe, generic messages at the handler boundary; log details server-side

```java
try {
    return orderService.findById(id);
} catch (OrderNotFoundException ex) {
    log.warn("Order not found: id={}", id);
    return ApiResponse.error("Resource not found");
} catch (Exception ex) {
    log.error("Unexpected error processing order id={}", id, ex);
    return ApiResponse.error("Internal server error");
}
```

## CI Integration

These run automatically in the verification loop (`verification.md`); listed here so the constraints above can be wired up.

### Dependency Scanning

- Audit transitive dependencies: `mvn dependency:tree` or `./gradlew dependencies`
- OWASP Dependency-Check plugin (Maven or Gradle) flags known CVEs in dependencies
- Snyk for SaaS scanning with PR bot integration
- Renovate or Dependabot for automated dependency updates

### Static Analysis

- SpotBugs plus the OWASP **find-sec-bugs** plugin (SpotBugs has no built-in security ruleset)
- SonarQube with security hotspots enabled

## Anti-Patterns

- Logging the full request body (often contains credentials or PII)
- Catching `Throwable` to swallow errors silently
- Returning database error messages to API clients (`SQLException.getMessage()` may leak schema info)
- Trusting user-supplied redirect URLs without allowlist validation
- Building JSON or SQL by string concatenation
