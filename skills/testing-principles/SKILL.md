---
name: testing-principles
disable-model-invocation: true
description: "Cross-stack testing principles — unit/integration/E2E boundaries, sociable vs solitary unit tests, narrow integration tests, isolation rules, F.I.R.S.T, naming, mocking schools, flaky prevention."
---

# Testing Principles

Stack-invariant testing principles. Language skills (`java-development`, `python-development`, `typescript-development`, `react-development`) point here for the reasoning and carry only their own syntax. E2E-specific patterns: Read `../e2e-testing/SKILL.md`.

## The Testing Ladder

| Layer | Dependencies | Entry point | Count |
| --- | --- | --- | --- |
| Unit | Awkward collaborators replaced by doubles | Direct function/method call | Many |
| Integration | Key collaborators real (DB via testcontainers); external boundaries mocked | Component interface / in-process app | Some |
| E2E | All real | Public interface (browser UI, running server's HTTP) | Few |

A fully real system behind its public entry point is E2E; mocked dependencies make a suite an integration test. API-level E2E patterns (three-layer assertions, auth fixtures): Read `../e2e-testing/references/backend-api.md`.

## Unit Tests: Sociable vs Solitary

- **Awkward collaborator**: slow, side-effectful, or non-deterministic — network, database, clock, filesystem, randomness
- **Solitary** (London, mockist): all collaborators replaced by test doubles; asserts interactions
- **Sociable** (classical, Chicago): only awkward collaborators are doubled; in-process collaborators stay real

Both are legitimate (Fowler). Default to sociable — double the awkward, keep the rest real, and keep the code under test real always. Mocking everything couples tests to implementation and makes refactoring painful; solitary fits when the interaction IS the contract.

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

Fast (milliseconds for unit, seconds for integration), Independent (any order, parallel-safe), Repeatable, Self-validating, Timely (written with the production code), plus Understandable (reads like a specification of the behavior).

## Structure and Naming

- **Arrange–Act–Assert** (given–when–then): set up data, call the subject, assert outcome — one behavior per test
- Name tests after the **behavior**: `createsOrder_persistsTotal` or "creates an order and persists the total" — not `test1` or `testCreateMethod`
- Test observable behavior through the public interface; private methods are implementation detail
- Don't test trivial code (getters/setters); don't assert internal call sequences unless the interaction IS the contract

## Flaky Prevention

Root causes: fixed sleeps instead of condition waits, shared mutable state, reliance on external/live services, concurrency races, animation/timing. Fixes: wait for conditions, isolate state, double externals, quarantine with a tracked issue and fix — do not delete silently.
