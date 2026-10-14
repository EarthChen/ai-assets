---
description: "Karpathy Rules: behavioral guidelines to reduce common LLM coding mistakes"
alwaysApply: true
---
# Karpathy Guidelines Rules

These rules apply to every coding task unless explicitly overridden.
**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**State assumptions. Surface confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them and let the user pick.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem.** Scope and abstraction follow YAGNI and KISS (see coding-style).

- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Leave adjacent code, comments, and formatting as found.
- Refactor only what is broken.
- If you notice unrelated dead code, mention it - leave it in place.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Remove pre-existing dead code only when asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Surface conflicts, don't average them
If two existing patterns in the codebase contradict, pick one (the more recent / more tested), explain why, and flag the other for cleanup.
"Average" code that satisfies both rules is the worst code.

## 6. Read before you write
Before adding code in a file, read the file's exports, the immediate caller, and any obvious shared utilities.
If you don't understand why existing code is structured the way it is, ask before adding to it.
"Looks orthogonal to me" is the most dangerous phrase in any codebase.

## 7. Tests verify intent, not just behavior
Every test must encode WHY the behavior matters, not just WHAT it does.
A test like `expect(getUserName()).toBe('John')` is worthless if the function takes a hardcoded ID.
If you can't write a test that would fail when business logic changes, the function is wrong.

## 8. Checkpoint at milestones
In a multi-step task, report what is done, what is verified, and what is left at each milestone, not after every tool call.
Continue only from a state you can describe back to me. If you lose track, stop and restate.

## 9. Match the codebase's conventions, even if you disagree
If the codebase uses snake_case and you'd prefer camelCase: snake_case.
If the codebase uses class-based components and you'd prefer hooks: class-based.
Disagreement is a separate conversation. Inside the codebase, conformance > taste.
If you genuinely think the convention is harmful, surface it instead of forking it silently.

## 10. Fail loud
If you can't be sure something worked, say so explicitly.
"Migration completed" is wrong if 30 records were skipped silently.
"Tests pass" is wrong if you skipped any.
"Feature works" is wrong if you didn't verify the edge case I asked about.
