---
name: feature-workflow
description: "Use when starting a feature or fix: plan → TDD → simplify → review → commit pipeline, with the user-run vs model-run split."
---

# Development Workflow

## When to Use

- You are starting a new feature or fix and need the full pipeline: plan → TDD → simplify → review → commit.
- You need the user-run planning commands (`/grill-with-docs`, `/to-spec`, `/to-tickets`), the model-invocable workflow skills (`grilling`, `domain-modeling`, `tdd`, the mattpocock `code-review` skill), the `code-simplifier` / `refactor-cleaner` agents, or the manual `code-simplify` / `refactor-clean` skills.
- For commit-message and PR conventions, use the `git-workflow` skill.

> This skill covers the feature development process that happens before git operations; the `git-workflow` skill covers the git operations.

The Feature Implementation Workflow describes the development pipeline: planning, TDD, code review, and then committing to git.

## Feature Implementation Workflow

Planning, TDD, and code review use workflow skills, not sub-agents. User-invoked skills cannot fire from another skill: the planning commands in step 1 run only when the user types them.

1. **Plan First**
   - Ask the user to run `/grill-with-docs` (align requirements + build the domain model), then `/to-spec` (synthesize the conversation into a spec), then `/to-tickets` (break it into tracer-bullet tickets)
   - If the user skips them, invoke the `grilling` skill to stress-test the plan, plus the `domain-modeling` skill when terminology matters
   - Identify dependencies and risks

2. **TDD Approach**
   - Use the `tdd` skill for the red-green-refactor loop; the coverage target is the global 80% testing rule

3. **Code Simplification**
   - Run the `code-simplifier` agent on the feature's git scope — uncommitted changes, recent commits, or the full branch diff against the merge target; include the `code-simplify` skill directory path in the dispatch prompt so the agent can load its `rules.md` (the agent probes standard install locations if no path is given)
   - Light-touch: reduce nesting, rename for clarity, remove proved-dead code in the changed region, consolidate duplicated logic in the touched files
   - Preserves exact behavior — tests of surviving behavior pass without modification
   - For whole-repo dead-code removal and structural refactoring across files, use the `refactor-cleaner` agent instead
   - `code-simplify` and `refactor-clean` are the human-invoked skills wrapping these two agents; the pipeline itself dispatches the agents (user-invoked skills cannot fire from another skill)

4. **Code Review**
   - Run the mattpocock `code-review` skill (`mattpocock-skills:code-review` on Claude; Standards + Spec axes) immediately after writing code
   - Address every Spec finding; fix or explicitly justify each Standards finding
   - For a deep severity-tiered audit, dispatch the `code-reviewer` agent; severity and approval rules live in the `code-quality-gate` skill

5. **Commit & Push**
   - Use the `git-workflow` skill for commit message format and PR process
