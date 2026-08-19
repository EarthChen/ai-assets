---
name: feature-workflow
description: "Feature development pipeline: plan → TDD → simplify → review → commit (grill-with-docs → to-spec → to-tickets → tdd → code-review skills). Use when starting a feature or fix."
---

# Development Workflow

## When to Use

- You are starting a new feature or fix and need the full pipeline: plan → TDD → simplify → review → commit.
- You need the workflow skills (`grill-with-docs`, `to-spec`, `to-tickets`, `tdd`, `code-review`), the `code-simplifier` / `refactor-cleaner` agents, or the manual `code-simplify` / `refactor-clean` skills.
- You are about to commit/push and want the commit-message and PR conventions.

> This rule extends the git workflow rule with the full feature development process that happens before git operations.

The Feature Implementation Workflow describes the development pipeline: planning, TDD, code review, and then committing to git.

## Feature Implementation Workflow

Planning, TDD, and code review use the locally installed workflow skills
(invoked by name), not sub-agents.

1. **Plan First**
   - Invoke the `grill-with-docs` skill to align requirements + build the domain model
   - Invoke the `to-spec` skill to synthesize the conversation into a spec
   - Invoke the `to-tickets` skill to break it into tracer-bullet tickets
   - Identify dependencies and risks

2. **TDD Approach**
   - Use the `tdd` skill for the red-green-refactor loop
   - Write tests first (RED)
   - Implement to pass tests (GREEN)
   - Refactor (IMPROVE)
   - Verify 80%+ coverage

3. **Code Simplification**
   - Run the `code-simplifier` agent on the feature's git scope — uncommitted changes, recent commits, or the full branch diff against the merge target; include the `code-simplify` skill directory path in the dispatch prompt so the agent can load its `rules.md` (the agent probes standard install locations if no path is given)
   - Light-touch: reduce nesting, rename for clarity, remove proved-dead code in the changed region, consolidate duplicated logic in the touched files
   - Preserves exact behavior — tests of surviving behavior pass without modification
   - For whole-repo dead-code removal and structural refactoring across files, use the `refactor-cleaner` agent instead
   - `code-simplify` and `refactor-clean` are the human-invoked skills wrapping these two agents; the pipeline itself dispatches the agents (user-invoked skills cannot fire from another skill)

4. **Code Review**
   - Use the `code-review` skill (dual-axis: Standards + Spec) immediately after writing code
   - Address CRITICAL and HIGH issues
   - Fix MEDIUM issues when possible

5. **Commit & Push**
   - Detailed commit messages
   - Follow conventional commits format
   - See the git workflow rule for commit message format and PR process
