---
name: feature-workflow
description: "Use before changing code that adds or alters behavior (feature, fix, strategy or schema change): plan → TDD → simplify → review → commit pipeline, with the user-run vs model-run split."
---

# Development Workflow

## When to Use

- You are starting a new feature or fix and need the full pipeline: plan → TDD → simplify → review → commit.
- You need the user-run planning commands (`/grill-with-docs`, `/to-spec`, `/to-tickets`), the model-invoked workflow skills (`grilling`, `domain-modeling`, `tdd`, the mattpocock `code-review` skill; each loads per the global "加载 Skill" rule), the `code-simplifier` / `refactor-cleaner` agents, or the manual `code-simplify` / `refactor-clean` skills.
- For commit-message and PR conventions, load the `git-workflow` skill.

> This skill covers the feature development process that happens before git operations; the `git-workflow` skill covers the git operations.

The Feature Implementation Workflow describes the development pipeline: planning, TDD, code review, and then committing to git.

## Feature Implementation Workflow

Planning, TDD, and code review use workflow skills, not sub-agents. Only the user fires user-invoked skills: the planning commands in step 1 run when the user types them. Model-invoked skills load per the global "加载 Skill" rule, one load per skill.

1. **Plan First**
   - Ask the user to run `/grill-with-docs` (align requirements + build the domain model), then `/to-spec` (synthesize the conversation into a spec), then `/to-tickets` (break it into tracer-bullet tickets), then `/implement-spec` (build every ticket on one integration branch); when the spec chain ran, continue at step 4 on that branch
   - If the user skips them, load the `grilling` skill to stress-test the plan; when terminology matters, also load the `domain-modeling` skill
   - Identify dependencies and risks

2. **TDD Approach**
   - Load the `tdd` skill for the red-green-refactor loop; the gate is the global testing rule (every agreed seam has a test; 80% coverage is a reference)

3. **Code Simplification**
   - Run the `code-simplifier` agent on the feature's git scope — uncommitted changes, recent commits, or the full branch diff against the merge target; include the `code-simplify` skill directory path and the words `apply` and `pipeline mode` in the dispatch prompt so the agent loads its `rules.md`, applies the findings, and stays inside Pipeline mode (the agent probes standard install locations if no path is given)
   - Pipeline mode edits only lines this change added or modified, plus residue this change made unused. Pre-existing dead code or duplication in the touched files is reported, not removed (global rule: remove pre-existing dead code only when asked)
   - Preserves exact behavior — tests of surviving behavior pass without modification
   - For whole-repo dead-code removal and structural refactoring across files, use the `refactor-cleaner` agent instead
   - `code-simplify` and `refactor-clean` are the human-invoked skills wrapping these two agents; the pipeline itself dispatches the agents (the user fires those skills)

4. **Code Review**
   - Immediately after writing code, load the mattpocock `code-review` skill (Claude Code name: `mattpocock-skills:code-review`) for the Standards + Spec axes
   - Address every Spec finding; fix or explicitly justify each Standards finding
   - Answer these about the diff before you call it reviewed. Standards review does not catch them, and the user has asked each one by hand:
     - Data access: does a new or changed query scan a whole table, run once per item in a loop, or add a call that a cheaper existing one covers?
     - Leftovers: does the change obsolete a field, branch, or config key? Remove it in the same change.
     - Stability: does a value that crosses a boundary (database, RPC, config) travel as an explicit code, not an enum name or ordinal?
     - Reuse: does existing logic already produce this result or display?
   - A diff that hits the security list in the `code-quality-gate` skill (Review standards) also gets the `code-reviewer` agent; this is mandatory
   - For a deep severity-tiered audit, dispatch the `code-reviewer` agent; severity and approval rules live in the `code-quality-gate` skill

5. **Commit & Push**
   - Load the `git-workflow` skill for commit message format and PR process
