---
name: agent-introspection-debugging
description: "Use when the same tool call fails 2+ times, a loop or tool-call limit is hit, or context bloat degrades output: capture, diagnose, contain, report."
---

# Agent Introspection Debugging

A workflow, not a runtime: debug your own failing run systematically before you retry or escalate. Not for framework-specific debugging, and never claim a recovery action (e.g. "reset agent state") that you did not perform with a real tool.

## Phase 1: Capture

Record the failure before any retry:

```markdown
## Failure Capture
- Goal in progress:
- Error (type, message, stack trace if any):
- Last successful step:
- Last failed tool / command:
- Repeated pattern seen:
- Environment assumptions to verify (cwd, branch, service state, expected files):
```

## Phase 2: Diagnose

Match the failure to a pattern before you change anything.

| Pattern | Likely cause | Check |
| --- | --- | --- |
| Tool-call limit / same command repeated | loop with no exit condition | last N tool calls for repetition |
| Context overflow / degraded reasoning | repeated plans, oversized logs | recent context for duplication and low-signal bulk |
| `ECONNREFUSED` / timeout | service down or wrong port | service health, URL, port |
| `429` / quota exhaustion | retry storm, no backoff | count of repeated calls, retry spacing |
| File missing after write / stale diff | wrong cwd or branch drift | path, cwd, `git status`, file existence |
| Tests still fail after "fix" | wrong hypothesis | isolate the exact failing test, re-derive the bug |

Classify: logic, state, environment, or policy failure? Deterministic or transient? Did you drift from the real objective?

## Phase 3: Contained Recovery

Take the smallest reversible action that tests the diagnosis, in this order:

1. Restate the real objective in one sentence.
2. Verify the world state (files, branch, processes) instead of trusting memory.
3. Shrink the failing scope to one command, one file, or one test.
4. Run one discriminating check.
5. Only then retry. Escalate to the human when the failure is high-risk or externally blocked.

Never retry the same action with slightly different wording.

## Phase 4: Report

Do not end with "I fixed it" alone:

```markdown
## Agent Self-Debug Report
- Failure:
- Root cause:
- Recovery action (and why it is safe):
- Evidence the situation is better or still blocked:
- Result: success | partial | blocked
- Follow-up / preventive change:
```
