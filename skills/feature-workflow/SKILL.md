---
name: feature-workflow
description: "Feature development pipeline: plan → TDD → simplify → review → commit. Use when starting a feature/fix: run /grill-with-docs, /to-spec, /to-tickets, /tdd, code-simplifier/refactor-cleaner, /code-review, then commit."
---

# Development Workflow

## When to Use

- You are starting a new feature or fix and need the full pipeline: plan → TDD → simplify → review → commit.
- You need the mattpocock/skills entry points (`/grill-with-docs`, `/to-spec`, `/to-tickets`, `/tdd`, `/code-review`) or the `code-simplifier` / `refactor-cleaner` agents.
- You are about to commit/push and want the commit-message and PR conventions.

> This rule extends the git workflow rule with the full feature development process that happens before git operations.

The Feature Implementation Workflow describes the development pipeline: planning, TDD, code review, and then committing to git.

## Feature Implementation Workflow

Planning, TDD, and code review use the mattpocock/skills workflow (native
plugin `mattpocock-skills@mattpocock` on Claude Code; vendored on
Codex/Cursor), not sub-agents.

1. **Plan First**
   - Run `/grill-with-docs` to align requirements + build the domain model
   - Run `/to-spec` to synthesize the conversation into a spec
   - Run `/to-tickets` to break it into tracer-bullet tickets
   - Identify dependencies and risks

2. **TDD Approach**
   - Use the `/tdd` skill for the red-green-refactor loop
   - Write tests first (RED)
   - Implement to pass tests (GREEN)
   - Refactor (IMPROVE)
   - Verify 80%+ coverage

3. **Code Simplification**
   - Run the `code-simplifier` agent on recently modified code for clarity, consistency, and maintainability
   - Light-touch: reduce nesting, rename for clarity, remove dead code in the changed region, consolidate duplicated logic in the touched files
   - Preserves exact behavior — all tests must still pass without modification
   - For whole-repo dead-code removal and structural refactoring across files, use the `refactor-cleaner` agent instead

4. **Code Review**
   - Use the `/code-review` skill (dual-axis: Standards + Spec) immediately after writing code
   - Address CRITICAL and HIGH issues
   - Fix MEDIUM issues when possible

5. **Commit & Push**
   - Detailed commit messages
   - Follow conventional commits format
   - See the git workflow rule for commit message format and PR process
