---
name: java-development
description: "Use when working on Java (Spring Boot / Quarkus): writing or reviewing code, verifying before release, or fixing a failing build."
---

# Java

Detect the framework first (build file: `spring-boot-starter-*` → Spring Boot, `quarkus-*` → Quarkus), then read only the reference matching the task branch.

## Routing

| Task branch | Reference to read |
| --- | --- |
| Naming, immutability, DI, reactive, exceptions, logging, config, test expectations | `references/coding-standards.md` |
| Spring Boot (only): error responses, rate limiting, production defaults | `references/patterns.md` |
| Spring Boot (only): test-first work, slice selection, Testcontainers, JaCoCo | `references/tdd.md` |
| Spring Boot (only): pre-release / pre-PR verification loop | `references/verification.md` |
| Spring Boot (only): code-level security | `references/security.md` |
| Build failing: compile errors, dependency conflicts, annotation processor / Spring / Quarkus build issues | `references/build-troubleshooting.md` |

Quarkus has no `patterns.md`, `tdd.md`, `verification.md`, or `security.md`; use `coding-standards.md` and `build-troubleshooting.md`.

## Always

- Test-first: Call the Skill tool with "tdd". Failing test → fix the implementation.
- Before any release or PR, run `references/verification.md`.

## Done

Framework detected, the matching reference read, and (when the work ships) the verification report reads READY.
