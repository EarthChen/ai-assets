# Task Intake & Triage

Intake turns whatever the user hands you — nothing, a spec, or a finished ticket set — into dispatchable briefs under `<swarm>/tasks/`. The orchestrator owns intake; workers never triage.

## Step 1 — Identify the source

| Source | Shape of plan.md | Who ticketizes |
| --- | --- | --- |
| Tickets exist (ticket files, issue list, spec/ticket artifacts) | Mapping table: ticket → task | nobody — wrap tickets as-is |
| Spec only | Same, after ticketization | orchestrator inline (≤ ~8 tickets) or one planner worker |
| Nothing | Decomposition from the goal: split by domain, one builder per code area with sharp boundaries | orchestrator |

Ask the user when ambiguous; confirm a ticket source exists before using it.

**Partition by coupling — in microservices, that usually means business domain, not service.** Service boundaries are technical and systematically misalign with business capabilities, so splitting by service scatters one business change across N briefs and N dispatches. Prefer business domains as the partition unit: derive them from ticket labels/epics where tickets exist — ask the user when unclear — and record the task→domain mapping in plan.md. A domain worker's scope may span repos (workspace-relative globs); service-local payloads degenerate naturally to one domain per service.

## Step 2 — Write briefs (thin wrapper)

When a ticket exists, the brief **wraps** it — preserve the ticket id, quote its intent, and add only the swarm fields. Never rewrite the ticket's substance away. Template for `<swarm>/tasks/<id>.md`:

```markdown
# <id> — <title>
ticket: <ticket id / path / URL, or "none">
domain: <business domain — may span repos>    deps: <task ids, or none>
execution: <how to work this task, free-form — a skill command in the target
  worker's platform syntax (platforms.md: Skill invocation), specific
  requirements, or both; omit when nothing special applies>
thinking: <level only if the task genuinely needs more than the pool default
  (low); omit otherwise>

## Goal
<what "done" means — quote the ticket where one exists>

## Inputs (paths)
<spec / contract / doc paths the worker must read>

## Scope boundary
<path globs this task owns; everything outside is someone else's files>

## Contracts
<<swarm>/contracts/<name>.md references, or none>

## Worktree
<swarm/<slug>-<id> branch + worktree path, or "base in-place" ("plan worktree in-place" when exiled — Worktrees), or "none (read-only)". Who commits: roles.md, builder>

## Definition of done
<checkable criteria, including the verification command to run>
```

Tasks without tickets use the same template with `ticket: none`.

**`execution:`** is free-form execution guidance. A skill command tells the worker to load and follow that skill — write it in the dispatched worker's platform syntax (platforms.md: Skill invocation); if the task later goes to a worker of another kind, rewrite the line at dispatch. Anything else is a binding requirement on how to work. Execution instructions the user gave at invocation are copied into briefs **verbatim** and outrank orchestrator defaults — the orchestrator only fills gaps at triage.

**`thinking:`** sets this task's reasoning demand when it departs from the pool default (`low`) — upward for genuinely hard tasks (ambiguous bugs, algorithmic cores, gnarly refactors). Omitting the line demands the pool default, so a high-level worker picking up a plain task steps back down (SKILL.md § Platforms). Omit unless the task genuinely departs from the default.

## Step 3 — Triage gate

Every brief gets exactly one verdict before queueing:

| Verdict | Meaning | Action |
| --- | --- | --- |
| `ready` | File-disjoint scope expressible, inputs as paths, checkable DoD | queue for dispatch |
| `needs-contract` | Domains touch without a written interface | write `<swarm>/contracts/<name>.md`, re-triage |
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

## Assigning by coupling

Work confined to one service: spawn `<slug>-wk-<service>` with its pane cwd at that repo, route same-service tasks to it by affinity, hot services get `<slug>-wk-<service>-<n>`. A cross-cutting business feature spanning many repos is ONE workstream, not N: assign it to one worker as a vertical slice, executed sequentially across repos — splitting it per repo manufactures N-way dispatch and coordination cost for one semantic change; split per repo only when contracts make the slices genuinely independent. A homogeneous mechanical sweep (dependency bump, mass rename, config sweep) is likewise ONE generic worker (`<slug>-wk-<change>`, workspace cwd) — script the change once, apply it across repos, handle the exceptions; batch into a few slices only when N is large, the work resists scripting, and wall time matters; never one worker per service. Cross-repo workers hold one active repo at a time. A worker whose next task lies in another repo cold-respawns under the same name at the new repo's cwd — pane cwd is fixed at spawn, and cross-repo warmth is worthless (SKILL.md: Pool discipline).
