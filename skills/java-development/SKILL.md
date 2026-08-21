---
name: java-development
description: "Java development conventions (Spring Boot / Quarkus) — coding standards, architecture patterns, TDD, pre-release verification, build error troubleshooting. Use when writing or reviewing Java code, or when a Java build fails."
---

# Java

Java conventions covering Spring Boot and Quarkus. Detect the framework first (build file: `spring-boot-starter-*` → Spring Boot, `quarkus-*` → Quarkus), then load only the reference matching the current task branch.

## Routing

| Task branch | Reference to read |
| --- | --- |
| Naming, immutability, Optional, streams, dependency injection, exceptions, generics | `references/coding-standards.md` |
| Spring Boot architecture: REST layering, repositories, services/transactions, DTOs/validation, caching, async | `references/patterns.md` |
| Test-first work: JUnit 5, Mockito, MockMvc, DataJpaTest, Testcontainers, JaCoCo | `references/tdd.md` |
| Pre-release / pre-PR: build → static analysis → tests + coverage → security scan → diff review | `references/verification.md` |
| Build failing: compile errors, dependency conflicts, annotation processor / Spring / Quarkus build issues | `references/build-troubleshooting.md` |

## Always

- `references/coding-standards.md` is the authority for naming, immutability, Optional, and DI — check it for every class touched.
- Red-green-refactor via the `tdd` skill; fix the implementation, not the failing test.
- Run the `references/verification.md` loop before any release or PR.

## Completion criterion

Framework detected, every changed class checked against the matching branch reference, and the verification loop green when the task ships.
