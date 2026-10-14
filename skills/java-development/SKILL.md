---
name: java-development
description: "Use when writing, reviewing, or pre-release verifying Java code (Spring Boot / Quarkus), or when a Java build fails."
---

# Java

Java conventions covering Spring Boot and Quarkus. Detect the framework first (build file: `spring-boot-starter-*` → Spring Boot, `quarkus-*` → Quarkus), then load only the reference matching the current task branch. `patterns.md`, `tdd.md`, `verification.md`, and `security.md` are Spring Boot-only; Quarkus is covered by `coding-standards.md` and `build-troubleshooting.md` only.

## Routing

| Task branch | Reference to read |
| --- | --- |
| Naming, immutability, Optional, streams, dependency injection, exceptions, generics | `references/coding-standards.md` |
| Spring Boot architecture (Spring Boot only): REST layering, repositories, services/transactions, DTOs/validation, caching, async | `references/patterns.md` |
| Test-first work (Spring Boot only): JUnit 5, Mockito, MockMvc, DataJpaTest, Testcontainers, JaCoCo | `references/tdd.md` |
| Pre-release / pre-PR (Spring Boot only): build → static analysis → tests + coverage → security scan → diff review | `references/verification.md` |
| Build failing: compile errors, dependency conflicts, annotation processor / Spring / Quarkus build issues | `references/build-troubleshooting.md` |
| Code-level security (Spring Boot only): secrets, SQL injection, input validation, auth, error messages | `references/security.md` |

## Always

- `references/coding-standards.md` is the authority for naming, immutability, Optional, and DI — check it for every class touched.
- Test-first via the `tdd` skill; coverage target is the global 80% testing rule; fix the implementation, not the failing test.
- Run the `references/verification.md` loop before any release or PR.

## Completion criterion

Framework detected, every changed class checked against the matching branch reference, and the verification loop green when the task ships.
