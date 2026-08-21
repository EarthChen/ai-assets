---
name: testing-principles
disable-model-invocation: true
description: "Cross-stack testing principles — unit/integration/E2E boundaries, sociable vs solitary unit tests, narrow integration tests, isolation rules, F.I.R.S.T, naming, mocking schools, flaky prevention. Reference material consumed by the language development skills."
---

# Testing Principles

Stack-invariant testing principles. Language skills (`java-development`, `python-development`, `typescript-development`) point here for the reasoning and carry only their own syntax. E2E-specific patterns live in the `e2e-testing` skill.

## The Testing Ladder

| Layer | Dependencies | Entry point | Count |
| --- | --- | --- | --- |
| Unit | Slow/side-effectful collaborators replaced by doubles | Direct function/method call | Many |
| Integration | Key collaborators real (DB via testcontainers); external boundaries mocked | Component interface / in-process app | Some |
| E2E | All real | Public interface (browser UI, running server's HTTP) | Few |

A fully real system behind its public entry point is E2E; mocked dependencies make a suite an integration test. API-level E2E patterns (three-layer assertions, auth fixtures): `~/.agents/skills/e2e-testing/references/backend-api.md`.

## Unit Tests: Sociable vs Solitary

- **Solitary**: all collaborators replaced by test doubles
- **Sociable**: only slow/side-effectful collaborators (database, network, filesystem) are doubled; in-process collaborators stay real

Both are legitimate (Fowler). Default to sociable — double what is slow or has side effects, keep the rest real. Mocking everything couples tests to implementation and makes refactoring painful.

## Narrow Integration Tests

One integration point per test. Broad tests (all services live) are system/E2E territory.

**Where to write them**: wherever data crosses a serialization boundary —

- REST/gRPC endpoints
- Database reads/writes
- Queue publishers/consumers
- Filesystem reads/writes
- External API clients

For external services that cannot run locally, test against a faithful double (WireMock/mountebank/nock) and pin its fidelity with contract tests (Pact) when the provider is another team.

## Isolation Rules

- **Default**: transaction rollback (begin → test → rollback) — fastest
- **Fallback**: per-test truncation/seeding when the code under test manages its own transactions or commits from other threads — rollback would hide those writes
- Unique-ID suffixes on all test data so parallel workers never collide
- Real databases via testcontainers — in-memory substitutes (H2, SQLite-for-Postgres) differ in dialect and behavior and hide production bugs

## F.I.R.S.T (+U)

- **Fast** — milliseconds for unit; seconds for integration
- **Independent** — no shared state, any order, parallel-safe
- **Repeatable** — same result on every machine, every run
- **Self-validating** — passes or fails without human inspection
- **Timely** — written with (not after) the production code
- **Understandable** — reads like a specification of the behavior

## Structure and Naming

- **Arrange–Act–Assert** (given–when–then): set up data, call the subject, assert outcome — one behavior per test
- Name tests after the **behavior**: `createsOrder_persistsTotal` or "creates an order and persists the total" — not `test1` or `testCreateMethod`
- Test observable behavior through the public interface; private methods are implementation detail
- Don't test trivial code (getters/setters); don't assert internal call sequences unless the interaction IS the contract

## What to Mock

- **Real**: database, cache, message broker (integration); pure in-process collaborators (unit)
- **Doubled**: slow/side-effectful dependencies — network calls, clocks, randomness, filesystem (where practical)
- **Never**: the code under test, the auth layer

Classical (Chicago) style doubles only what is awkward; London (mockist) style mocks all collaborators and asserts interactions. Classical produces less brittle tests — prefer it unless interaction is the contract.

## Flaky Prevention

Root causes in order of frequency: fixed sleeps instead of condition waits, shared mutable state, reliance on external/live services, concurrency races, animation/timing. Fixes: wait for conditions, isolate state, double externals, quarantine with a tracked issue and fix — do not delete silently.

## Test Data

- **Test Data Builder**: builder per entity with sensible defaults; tests override only what they assert on
- **Object Mother**: named factory methods for canonical fixtures (`aValidOrder()`, `anExpiredCart()`)
- Prefer builders over raw constructors repeated across tests; prefer fresh data over mutating shared fixtures
