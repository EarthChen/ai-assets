---
name: testing-principles
disable-model-invocation: true
description: "Cross-stack testing principles — unit/integration/E2E boundaries, run-the-change verification, property and differential tests, sociable vs solitary unit tests, narrow integration tests, isolation rules, F.I.R.S.T, naming, mocking schools, flaky prevention."
---

# Testing Principles

Stack-invariant testing principles. Language skills (`java-development`, `python-development`, `typescript-development`, `react-development`) point here for the reasoning and carry only their own syntax. E2E task (browser via Playwright, or API against a running server): Read `../e2e-testing/SKILL.md`.

## The Testing Ladder

| Layer | Dependencies | Entry point | Count |
| --- | --- | --- | --- |
| Unit | Awkward collaborators replaced by doubles | Direct function/method call | Many |
| Integration | Key collaborators real (DB via testcontainers); external boundaries mocked | Component interface / in-process app | Some |
| E2E | All real | Public interface (browser UI, running server's HTTP) | Few |

A fully real system behind its public entry point is E2E; mocked dependencies make a suite an integration test.

## Verification Means Running the Change

Green unit and integration suites do not verify a change: tests and author share the same blind spot, so a feature can break while everything passes. Verify a change by running the real system through its public interface — the whole feature works or it does not, and the failure names what broke. Verify against a **feature map**: the flows a user takes, each with its path, action, and expected result. It guides what to run and grades the evidence — write it from the requirement or the diff before running, and keep it next to the feature's E2E specs. The ladder's counts govern the regression suite; the verification of a single change is E2E-first.

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

## Property Tests

State a property that cannot be false, then let a generation library throw thousands of inputs at it — generated inputs do not share the author's bias, so they reach the edge cases hand-picked examples miss. Recurring properties:

- **Round-trip**: encode then decode returns the input (serialization, parsing)
- **Invariant**: holds after every operation (balance never negative, output always sorted)
- **Idempotency**: running a migration, normalization, or retry twice equals running it once
- **Equivalence**: the optimized path matches the naive-but-correct reference

Libraries: fast-check (JS/TS), Hypothesis (Python), jqwik (Java).

## Differential Tests

The old system is the oracle. Run the old and new implementations on the same inputs and diff the outputs — every divergence is a bug or a breaking change. The fit is migrations and rewrites whose spec has drifted from production behavior and no longer verifies anything. Feed random inputs or a sample of real traffic, normalize irrelevant differences (whitespace, ordering), and keep an approved-changes list for divergences the new system is meant to produce.

## Isolation Rules

- **Default**: transaction rollback (begin → test → rollback) — fastest
- **Fallback**: per-test truncation/seeding when the code under test manages its own transactions or commits from other threads — rollback would hide those writes
- Unique-ID suffixes on all test data so parallel workers never collide
- Real databases via testcontainers — in-memory substitutes (H2, SQLite-for-Postgres) differ in dialect and behavior and hide production bugs

## F.I.R.S.T (+U)

Fast (milliseconds for unit, seconds for integration — fast enough to run on every save), Independent (any order, parallel-safe — a test never depends on another's side effects or leftovers), Repeatable, Self-validating, Timely (written with the production code), plus Understandable (reads like a specification of the behavior).

## Structure and Naming

Four phases, each a few lines — **Arrange–Act–Assert–Cleanup** (given–when–then, then restore what was acquired). Simple enough to read at a glance; it needs no test of its own:

```text
// Arrange: an empty cart, an item priced 50
// Act: add the item twice
// Assert: cart.total == 100
// Cleanup: rollback the transaction (isolation policy above)
```

- Name tests after the **behavior**: `createsOrder_persistsTotal` or "creates an order and persists the total" — not `test1` or `testCreateMethod`. The suite is the module's **living documentation**: names and assertions tell a new developer the contract — inputs, outputs, business rules.
- Test observable **behavior** through the public interface; private state and internal call sequences are implementation detail. Assert the contract, so a behavior-preserving refactor keeps the suite green:

```text
// asserts the mechanism — breaks on every refactor
assert invoice.taxRateField == 0.13
// asserts the behavior — survives refactor
assert invoice.total == 113.00
```

- Don't test trivial code (getters/setters); don't assert internal call sequences unless the interaction IS the contract.

## Flaky Prevention

Root causes: fixed sleeps instead of condition waits, shared mutable state, reliance on external/live services, concurrency races, animation/timing. Never mask a failure with sleeps or retry-until-green — that trains future runs to rerun instead of repair. Fixes: wait for conditions, isolate state, double externals, quarantine with a tracked issue and fix. A flaky test whose root cause cannot be found is deleted, with the reason recorded.
