# Task Intake & Triage

Intake turns whatever the user hands you — nothing, a spec, or a finished ticket set — into dispatchable briefs under `.herdr-swarm/tasks/`. The orchestrator owns intake; workers never triage.

## Step 1 — Identify the source

| Source | Shape of plan.md | Who ticketizes |
| --- | --- | --- |
| Tickets exist (ticket files, issue list, spec/ticket artifacts) | Mapping table: ticket → task | nobody — wrap tickets as-is |
| Spec only | Same, after ticketization | orchestrator inline (≤ ~8 tickets) or one planner worker |
| Nothing | Decomposition from the goal | orchestrator |

Ask the user when ambiguous — never guess a ticket source into existence.

## Step 2 — Write briefs (thin wrapper)

When a ticket exists, the brief **wraps** it — preserve the ticket id, quote its intent, and add only the swarm fields. Never rewrite the ticket's substance away. Template for `.herdr-swarm/tasks/<id>.md`:

```markdown
# <id> — <title>
ticket: <ticket id / path / URL, or "none">
domain: <business domain — may span repos>    deps: <task ids, or none>
execution: <how to work this task, free-form — a skill command like /skill:tdd,
  specific requirements, or both; omit when nothing special applies>

## Goal
<what "done" means — quote the ticket where one exists>

## Inputs (paths)
<spec / contract / doc paths the worker must read>

## Scope boundary
<path globs this task owns; everything outside is someone else's files>

## Contracts
<.herdr-swarm/contracts/<name>.md references, or none>

## Worktree
<swarm/<id> branch + worktree path, or "base in-place", or "none (read-only)">

## Definition of done
<checkable criteria, including the verification command to run>
```

Tasks without tickets use the same template with `ticket: none`.

**`execution:`** is free-form execution guidance. A skill command (e.g. `/skill:tdd`) tells the worker to load and follow that skill; anything else is a binding requirement on how to work. Execution instructions the user gave at invocation are copied into briefs **verbatim** and outrank orchestrator defaults — the orchestrator only fills gaps at triage (e.g. `/skill:tdd` for feature/fix builders).

## Step 3 — Triage gate

Every brief gets exactly one verdict before queueing:

| Verdict | Meaning | Action |
| --- | --- | --- |
| `ready` | File-disjoint scope expressible, inputs as paths, checkable DoD | queue for dispatch |
| `needs-contract` | Domains touch without a written interface | write `.herdr-swarm/contracts/<name>.md`, re-triage |
| `needs-split` | Too big for one context window | split into subtasks, or mark for brokered dispatch |
| `blocked-info` | Missing decision only the user has | ask the user; park |

**Size gate (heuristic):** a brief estimated to touch >15 files or carry >3 independent sub-goals is `needs-split`. Homogeneous bulk work (the same mechanical edit across many files) may pass at your judgment — record the reason in plan.md notes so the decision survives compaction.

## Step 4 — plan.md

```markdown
# Swarm Plan
goal: <one line>
source: tickets|spec|goal
spec: <spec path(s), if any>

| task | ticket | domain | deps | verdict | scope (globs) | worktree | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
```

Update verdicts and notes as triage and execution proceed. `plan.md` + `ledger.md` together must let a fresh orchestrator session resume cold.
