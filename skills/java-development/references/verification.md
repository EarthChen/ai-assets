# Spring Boot Verification Loop

Run before PRs, after major refactors or dependency upgrades, and pre-deploy. Stop at the first failing phase; fix it; restart from that phase.

## Phase 1: Format (only if Spotless is configured)

```bash
mvn spotless:apply
./gradlew spotlessApply
```

Run first: formatting changes files, so it must precede the build and tests.

## Phase 2: Build

```bash
mvn -T 4 clean compile
./gradlew clean classes
```

## Phase 3: Static Analysis

Run only the plugins the build file configures (a missing plugin fails the run):

```bash
mvn -T 4 spotbugs:check pmd:check checkstyle:check
./gradlew checkstyleMain pmdMain spotbugsMain
```

## Phase 4: Tests + Coverage

```bash
mvn -T 4 verify   # tests + JaCoCo report + check (fails below 80% line coverage; snippet in tdd.md)
./gradlew test jacocoTestReport
```

Report total tests, passed/failed, and line/branch coverage.

## Phase 5: Security Scan

```bash
# Dependency CVEs
mvn org.owasp:dependency-check-maven:check
./gradlew dependencyCheckAnalyze

# Secrets in source
grep -rn "password\s*=\s*\"" src/ --include="*.java" --include="*.yml" --include="*.properties"
grep -rn "sk-\|api_key\|secret" src/ --include="*.java" --include="*.yml"
git secrets --scan  # if configured

# Raw exception messages in responses, stdout logging, wildcard CORS
grep -rn "e\.getMessage()" src/main/ --include="*.java"
grep -rn "System\.out\.print" src/main/ --include="*.java"
grep -rn "allowedOrigins.*\*" src/main/ --include="*.java"
```

## Phase 6: Diff Review

```bash
git diff --stat
git diff
```

Check: no debug output left, meaningful errors and HTTP statuses, transactions and validation where needed, config changes documented.

## Output Template

```
VERIFICATION REPORT
===================
Format:    [PASS/SKIP]
Build:     [PASS/FAIL]
Static:    [PASS/FAIL/SKIP] (spotbugs/pmd/checkstyle)
Tests:     [PASS/FAIL] (X/Y passed, Z% coverage)
Security:  [PASS/FAIL] (CVE findings: N)
Diff:      [X files changed]

Overall:   [READY / NOT READY]

Issues to Fix:
1. ...
```

READY means: Build and Tests PASS, coverage is at least 80%, Static is PASS or SKIP, and Security has no unhandled CVE with CVSS 7.0 or higher (adjust the threshold to the project's policy).
