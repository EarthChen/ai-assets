# Testing Requirements

Applies to changes in executable code. Documentation-only and configuration-only changes are exempt.

- TDD is mandatory for new features and bug fixes — the red-green-refactor loop is carried by the `tdd` skill (part of the `feature-workflow` skill pipeline).
- **Testing principles** (ladder boundaries, isolation, flaky prevention, property/differential tests, run-the-change verification): Read the `testing-principles` skill's `SKILL.md` from the platform skills directory (`~/.claude/skills/` on Claude, `~/.agents/skills/` elsewhere).
- **The gate**: every seam agreed in the `tdd` loop has a test. When no `tdd` loop ran (for example a refactor), list the seams the change touches and confirm them with the user before you mark the work done.
- **Run the change**: a behavior-affecting change is not done until the real system runs the affected flow through its public interface — "all tests pass" alone is not evidence (E2E: Read the `e2e-testing` skill's `SKILL.md` from the same platform skills directory). If the project has no verify skill (boots, drives, and inspects the running app), offer to create one.
- **Failure bound**: after 3 rounds of the same check still failing, stop fixing and report to the user with the failure evidence.
- **Coverage is a reference**: when the project has a coverage command, report line coverage against 80%. Do not block on it, do not add coverage tooling for it, and do not write tests only to raise it.
- **A project-configured coverage gate must pass**: run the project's full verification command (the one that runs every configured check), not the test command alone. When that gate fails, propose the uncovered seams to the user, test the ones the user confirms, and never lower the gate. If the user confirms none, stop and report the failing gate.
