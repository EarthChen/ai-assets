---
description: "Development workflow: plan, TDD, review, commit pipeline"
alwaysApply: true
---
# Development Workflow

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

3. **Code Review**
   - Use the `/code-review` skill (dual-axis: Standards + Spec) immediately after writing code
   - Address CRITICAL and HIGH issues
   - Fix MEDIUM issues when possible

4. **Commit & Push**
   - Detailed commit messages
   - Follow conventional commits format
   - See the git workflow rule for commit message format and PR process
