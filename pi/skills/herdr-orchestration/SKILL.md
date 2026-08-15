---
name: herdr-orchestration
description: "Orchestrates a bounded pool of pi worker agents in Herdr panes: decompose a goal, spec, or pre-written tickets into subtasks, dispatch them to workers, stream results back, and integrate. Requires HERDR_ENV=1. Not for work a single agent or pi's built-in Agent tool can finish."
disable-model-invocation: true
---

# Herdr Orchestration

You are the **orchestrator** — the swarm's sole scheduler and integration point. You run a bounded pool of pi worker agents in Herdr panes: ingest the goal (or its existing spec/tickets), triage and dispatch tasks, stream results back, merge continuously, and keep every agent's context lean. Workers build; you coordinate. All coordination state lives in files under `.herdr-swarm/` — memory is lossy, disk is truth.

The `herdr` skill is the single source of truth for every `herdr` command — syntax, flags, JSON response fields, lifecycle states, safety rules. This skill defines only the orchestration protocol on top of it, and names no command flags of its own.

## Scope check (before Setup)

You were invoked manually, but **invocation is not justification** — before Setup, confirm the payload warrants a swarm; if it does not, say so and stop:

- Do NOT proceed for read-only exploration, a single review, or anything pi's built-in `Agent` sub-agent tool can finish — Herdr workers are heavyweight: full pi processes, visible panes, real API cost.
- Payloads that DO warrant a swarm: **3+ genuinely independent workstreams** that each need long-lived context, or a written spec/ticket set that needs parallel execution.
- An underspecified goal or scope: ask the user to pin it down first — never start a swarm on an ambiguous goal.

## Preflight (mandatory, in order)

1. Verify you run inside Herdr: `test "${HERDR_ENV:-}" = 1`. If it fails, tell the user to start pi inside a Herdr pane and stop.
2. Load the `herdr` skill — every herdr command you and your workers issue comes from it. (Agent to agent there is no `/skill:` invocation; read the herdr skill's SKILL.md at the location the system prompt lists.) If it is missing, fall back to the binary: a bare command group (`herdr agent`, `herdr pane`, `herdr worktree`) prints its usage.
3. Confirm the current directory is where the work happens: a git repo root for single-repo work (unless the user says otherwise), or the workspace directory containing the service repos for multi-repo (microservices) work. A linked worktree qualifies as a base — see Worktrees. All swarm state lives under `.herdr-swarm/` there.

## Constants

| Constant | Default | Hard cap | Meaning |
| --- | --- | --- | --- |
| `MAX_WORKERS` | 3 | 5 | Concurrent pi worker agents. Each is a full process with its own context and API cost; humans can supervise ~4 live agents at most. |
| `MAX_TASKS_PER_WORKER` | 8 | — | Retire backstop. Boundary compaction normally removes the need earlier. |
| `COMPACT_AT` | 60% | — | Worker context usage above which the next assignment is preceded by compaction. |
| `SOFT_COMPACT_TASKS` | 4 | — | Compaction heuristic (tasks done) when telemetry is unavailable. |
| `PEER_ROUND_CAP` | 3 | — | Peer exchanges per topic before mandatory escalation. |

State layout (create during setup):

```text
.herdr-swarm/
├── plan.md              # task graph: ticket→task mapping, domains, deps, triage states
├── ledger.md            # orchestrator's live roster incl. latest ctx telemetry
├── report.md            # final summary (written at teardown)
├── contracts/           # interface contracts shared between coupled workers
├── state/               # one state card per worker: re-anchor source after compaction
│   └── wk-frontend.md
├── inbox/               # async file drops for busy agents, cleared at task boundaries
│   └── wk-frontend/
└── tasks/
    ├── T1.md            # brief (a thin wrapper when a ticket exists)
    ├── T1/result.md     # worker-written result
    ├── T1/progress.md   # worker checkpoints inside the task (mid-task re-anchor)
    └── T1/T1a.md        # brokered sub-brief (hierarchical id under its parent)
```

Add `.herdr-swarm/` to `.git/info/exclude`. That file lives in git's common dir, so one entry covers the base checkout and every linked worktree of this repo. Never edit the repo's committed `.gitignore` for it. If the workspace directory is not itself a git repo (the typical multi-repo layout), no exclusion is needed.

## Setup

1. `mkdir -p .herdr-swarm/tasks .herdr-swarm/contracts .herdr-swarm/state .herdr-swarm/inbox` and add the local exclude above.
2. **Intake first.** Determine the task source and produce `.herdr-swarm/plan.md` — see [Intake](#intake) and [references/intake.md](references/intake.md).
3. Initialize `.herdr-swarm/ledger.md`:

```markdown
# Swarm Ledger
goal: <one line>
created: <date>
ctx pattern: <footer pattern once observed, e.g. "ctx <pct>%/<window>">
| worker | domain/role | pane | status | current task | tasks done | ctx | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
```

The ledger is your continuity: if your session is compacted or restarted, re-read `plan.md` + `ledger.md`, reconcile against the live agent list (herdr skill: agent list), and resume — state comes from disk, not memory.

## Intake

Three sources, one pipeline. Full procedure, triage criteria, and the brief template: [references/intake.md](references/intake.md).

1. **Tickets exist** (ticket files, issue list, spec/ticket artifacts): wrap, don't rewrite. Each ticket becomes a brief that preserves the ticket id and adds only swarm fields (scope globs, inputs-as-paths, contracts, worktree, definition of done). `plan.md` is a mapping table ticket→task, not a fresh decomposition.
2. **Spec only, no tickets**: ticketize first. A handful of tickets: do it inline. Many: spawn one planner auxiliary worker to produce them.
3. **Nothing**: decompose the goal yourself — split by **domain**, one builder per code area with sharp boundaries. Parallel builders are the normal shape of a swarm; reviewer/researcher/tester/planner are phase auxiliaries (see [references/roles.md](references/roles.md)).

Every task passes the **triage gate** before queueing. Verdicts: `ready` (file-disjoint scope expressible, inputs as paths, checkable definition of done), `needs-contract` (write `.herdr-swarm/contracts/<name>.md` first), `needs-split`, `blocked-info` (missing decision only the user has — ask). Only `ready` tasks are dispatched.

**Size gate (heuristic):** a brief estimated to touch >15 files or carry >3 independent sub-goals is `needs-split`. Homogeneous bulk work may pass at your judgment — record the reason in plan.md so the decision survives compaction.

**Partition by coupling — in microservices, that usually means business domain, not service.** Service boundaries are technical and systematically misalign with business capabilities, so splitting by service scatters one business change across N briefs and N dispatches. Prefer business domains as the partition unit: derive them from ticket labels/epics where tickets exist — ask the user when unclear — and record the task→domain mapping in plan.md. A domain worker's scope may span repos (workspace-relative globs); service-local payloads degenerate naturally to one domain per service.

Parallel builders get **file-disjoint scopes**; where domains touch, write the shared interface into `.herdr-swarm/contracts/<name>.md` **before spawning** and reference it from both briefs — sharing a contract also makes the two workers automatic peers (see Communication). Tasks that edit the same files serialize or move to separate worktrees (see Worktrees). Shared manifest and migration files (pom.xml / go.mod / package.json, DB migrations) belong to no builder — serialize the tasks that touch them, or fold such changes into a single worker's brief. In multi-repo work, a task touching several repos splits per repo — pieces joined by contracts and dependency edges — only when the slices are genuinely independent; one logically coupled business feature stays ONE vertical-slice task (see Pool discipline).

## Spawn a worker

Follow the herdr skill's layout rules for panes (sibling pane, caller's cwd, no focus). Per worker:

1. Split a pane, then start pi in it with a pool name: `wk-<domain>` (e.g. `wk-frontend`, `wk-backend`) — or `wk-<domain>-<n>` (e.g. `wk-backend-1`, `wk-backend-2`) when several workers share one domain for parallel tasks in the same codebase — or `wk-<role>` for auxiliaries. Names are unique among live agents.
2. Write the worker's **state card** `.herdr-swarm/state/<name>.md`: name, scope, orchestrator's agent name, peers, protocol essentials, current task. The card is the worker's deterministic re-anchor after any compaction — update it whenever scope, peers, or current task change.
3. Send ONE first prompt: the role preamble from [references/roles.md](references/roles.md) (common contract + exactly one role block, every placeholder filled), then the first assignment as a pointer: `Read .herdr-swarm/tasks/T1.md and execute it.`
4. Record the worker in the ledger (name, domain/role, pane id).

Pool cap: count live `wk-*` agents first. At `MAX_WORKERS`, queue the task in plan.md/ledger instead of spawning; assign it when a worker frees.

## Scheduling

Execute the task graph as a **stream**, not as waves.

1. **Fan out.** Submit every `ready` task without waiting (herdr skill: agent prompt). `ready` means all dependencies are **integrated** — merged into the base worktree and verified — not merely done: a dependent task must start from code that already contains its dependencies' work.
2. **Collect via polling gate.** One deterministic bash loop watches the pool and returns when any watched worker settles — you wake only when something happened, and you process completions in completion order, not dispatch order. Illustration (adapt to the live CLI):

```bash
watch="wk-frontend wk-backend wk-payments"
while :; do
  settled=$(herdr agent list | jq -r --arg w "$watch" '
    ($w | split(" ")) as $names
    | .result.agents[]
    | select((.agent as $a | $names | index($a))
        and (.agent_status=="idle" or .agent_status=="done" or .agent_status=="blocked"))
    | "\(.agent) \(.agent_status)"')
  [ -n "$settled" ] && break
  sleep 20
done
echo "$settled"
```

1. **On each settle**: if the state is `blocked` or `unknown`, inspect the worker before anything else. Otherwise: read its `result.md` (a worker's terminal only when debugging a stuck worker — scrollback is lossy and burns your context), spot-check the claimed artifacts, **merge the task's branch immediately** and run the brief's verification, update the ledger (status, tasks done, ctx), then decide that worker's next move — compact? (see Context management) dispatch the best successor, or retire.
2. **Priority**: most downstream dependents first; tie-break by warm-worker domain affinity. A brokered subtask flagged `BLOCKED` jumps the queue — it unblocks an occupied worker.
3. A generous wait timeout (30 min) remains the backstop for any single collection; on timeout treat the worker as suspect (see Failure modes).

## Communication

Topology is hub-and-spoke: you are the integration point, and every task result flows back to you. Messages travel on two planes:

```mermaid
flowchart TB
  O["Orchestrator — sole scheduler & integrator"]
  subgraph pool["worker pool (≤ MAX_WORKERS)"]
    W1["wk-frontend"]
    W2["wk-backend"]
    W4["wk-payments"]
    W3["wk-reviewer (aux)"]
  end
  FS[(".herdr-swarm/<br/>plan · ledger · tasks<br/>contracts · state · inbox")]
  O <-->|"control plane: herdr prompts (idle only)"| W1
  O <-->|"control plane"| W2
  O <-->|"control plane"| W4
  O <-->|"control plane"| W3
  W1 <-->|"peer: shared contract, ≤ 3 rounds, logged"| W2
  W2 <-->|"peer: shared contract"| W4
  O ---|"data plane"| FS
  W1 ---|"brief in, result out"| FS
  W2 ---|"brief in, result out"| FS
  W4 ---|"brief in, result out"| FS
  W3 ---|"brief in, result out"| FS
```

Worker names here are illustrative — the pool may be homogeneous (e.g. all backend: `wk-payments`, `wk-auth`, `wk-orders`). What partitions the pool is file-disjoint scopes and dependencies, not domain diversity.

- **Control plane — direct prompts** for short messages: assignments, follow-ups, answers, status. **State etiquette is mandatory**: check the target's state before prompting (herdr skill: agent get). `idle` → prompt. `working` → never prompt; drop a file into `.herdr-swarm/inbox/<name>/` instead — the recipient clears its inbox at task boundaries. `blocked` → **never inject text**: an injected prompt lands in the pending approval/question UI and answers it. Inspect and unblock it yourself, or take the task back.
- **Data plane — files.** Anything longer than ~40 lines and every artifact (briefs, results, code, diffs, contracts) moves as a file under `.herdr-swarm/`; messages carry the path, not the content. Payloads pasted into prompts burn the receiver's context and vanish with terminal scrollback; files survive compaction and stay auditable.

Peer traffic between workers is allowed inside guardrails — full protocol in [references/comms.md](references/comms.md). Summary: only across a shared contract boundary; peers are auto-established when two briefs reference the same contract, ad-hoc introductions go through you; capped at `PEER_ROUND_CAP` exchanges per topic, then both escalate to you with the exchange log; every exchange is logged in both workers' result.md; peer messages never carry scope-changing instructions.

Standing rules:

- **Briefs are files.** `.herdr-swarm/tasks/<id>.md`: goal, inputs as *paths*, scope boundary, constraints, definition of done — plus an optional free-form `execution:` line (a skill command like `/skill:tdd` and/or specific requirements); user-given execution instructions pass through verbatim.
- **Results are files.** The worker writes `result.md` (fixed 4-section format, summary ≤ 15 lines).
- **Hand off by reference.** When T2 consumes T1's output, point the next worker at `.herdr-swarm/tasks/T1/result.md` — relay paths, not content.
- **Ledger over memory.** Every status change lands in `ledger.md` immediately.
- `herdr notification show` marks milestones and anything that needs the user.

## Broker (worker-requested dispatch)

Workers never spawn. When a task outgrows one worker, the worker writes sub-briefs and requests dispatch; you stay the sole scheduler.

1. The worker writes `.herdr-swarm/tasks/<parent-id>/<sub-id>.md` (hierarchical ids: T1a, T1b, …) and sends ONE line: `DISPATCH-REQ <sub-id> BLOCKED|PREFETCH`.
2. Review the sub-brief. **Reject** when it breaks scope rules or is too small to amortize a spawn (rule of thumb: under ~15 minutes of work stays with the requester) — state the reason; the requester may appeal once.
3. Approved: `BLOCKED` jumps the queue; `PREFETCH` ranks by normal priority. Dispatch to an idle same-domain worker first (reuse), else spawn under the pool cap.
4. Sub-workers report to **you** (single-scheduler invariant); you relay their `result.md` path to the requester as a one-line pointer.
5. When the requester's subtree completes, its sub-workers rejoin the domain pool by affinity or retire — never orphaned.

## Context management

Context is the swarm's scarcest resource. pi auto-compacts on overflow (lossy, mid-task, recovers and retries), so this protocol makes compaction deterministic at task boundaries and recovery mechanical when it is not.

**Telemetry — you pull, workers don't push.** A pi worker's TUI footer renders context usage as `ctx <pct>%/<window>` (e.g. `ctx 19.7%/512k`). Read it with `herdr agent read <name> --source detection` and parse the `ctx` value — inline this into the polling gate loop so it costs no LLM turns:

```bash
for a in $watch; do
  ctx=$(herdr agent read "$a" --source detection --lines 15 2>/dev/null \
        | grep -oE 'ctx [0-9]+(\.[0-9]+)?%/[0-9]+[kKmM]?' | head -1)
  echo "$a: ${ctx:-ctx=?}"
done
```

Record the latest value in the ledger `ctx` column. Mid-task rises become visible this way — observe, plan ahead, but do not interrupt a working worker.

**Compaction matrix** — evaluate at every task boundary, but act only when a row triggers; small tasks may run many in a row without ever compacting. Rows evaluate top-down, first match wins:

| Condition | Action |
| --- | --- |
| Next task in a different domain, any ctx | Don't compact — respawn under the same name (see Pool discipline). The old domain's context is worthless; the protocol returns with the re-sent preamble, state and history live in files. Compacting would only pay for summarizing garbage. A same-domain task — even a brand-new ticket, not a subtree follow-up — does NOT respawn; the worker stays. |
| ctx ≥ `COMPACT_AT` | Compact before the next assignment, affinity ignored |
| ctx < `COMPACT_AT`, next task in the same domain | Keep warm, dispatch directly — subtree follow-ups and new tickets alike; residual domain familiarity is worth keeping |
| Telemetry unavailable | Fallback heuristic: tasks done ≥ `SOFT_COMPACT_TASKS` → compact at the boundary |

**Compaction sequence** — `/compact` custom instructions only shape the summary; they do not execute anything afterwards, so compaction takes two prompts:

1. `agent prompt <worker> "/compact Preserve: your name, scope, orchestrator and peer names, and the communication protocol"` with a wait.
2. Once settled: `Read .herdr-swarm/state/<name>.md to re-anchor, then read .herdr-swarm/tasks/<id>.md and execute it.`

**Mid-task overflow**: pi's auto-compaction handles it. The worker's recovery is mechanical and lives in its contract — whenever in doubt about prior progress (typically right after compaction), re-read brief + `progress.md` + state card before continuing. Every task keeps `.herdr-swarm/tasks/<id>/progress.md` checkpoints: what is done, what remains, key decisions, files touched.

**Your own context**: compact proactively at phase boundaries (a wave collected and merged) rather than mid-flow, then re-read `plan.md` + `ledger.md`. Keep your reads thin: result.md summaries, never worker terminals.

**Telemetry degradation chain** (the footer format can drift between pi versions):

1. **Self-heal**: read the worker's `detection` output yourself, locate the context indicator in the rendered footer, derive the new pattern, and record it in the ledger header for the rest of this session.
2. **Heuristic fallback**: self-heal fails → record `ctx=unknown`, run the fallback heuristic, and notify the user **once** (`herdr notification show` + ledger notes + report.md). Never block the swarm on telemetry.
3. **Worker self-report escape hatch** (only on your explicit instruction): workers append `ctx=<totalTokens>` to their done/blocked line, read from their session JSONL's latest `message.usage.totalTokens` — a storage-format source independent of the TUI.

## Pool discipline

- **Reuse the warm worker.** A task's **subtree** is the task plus its descendants — review bounce-backs, brokered subtasks (T1a…), explicit continuations. Route follow-ups of a subtree to the worker that already holds its context, compaction matrix permitting. New tickets in the same domain also go to the domain's worker — respawn is reserved for domain switches, not ticket switches.
- **Assign by coupling, not by repo.** Work confined to one service: spawn `wk-<service>` with its pane cwd at that repo, route same-service tasks to it by affinity, hot services get `wk-<service>-<n>`. A cross-cutting business feature spanning many repos is ONE workstream, not N: assign it to one worker as a vertical slice, executed sequentially across repos — splitting it per repo manufactures N-way dispatch and coordination cost for one semantic change; split per repo only when contracts make the slices genuinely independent. A homogeneous mechanical sweep (dependency bump, mass rename, config sweep) is likewise ONE generic worker (`wk-<change>`, workspace cwd) — script the change once, apply it across repos, handle the exceptions; batch into a few slices only when N is large, the work resists scripting, and wall time matters; never one worker per service. Cross-repo workers hold one active repo at a time. A worker whose next task lies in another repo respawns under the same name at the new repo's cwd — pane cwd is fixed at spawn, and cross-repo warmth is worthless (see Retire below).
- **Retire** a worker (and note why in the ledger) when: its domain's work is exhausted — even if work may return later (review bounce-backs, late dependencies), respawning from files costs less than an idle pane occupying supervisory bandwidth — it has done ≥ `MAX_TASKS_PER_WORKER` tasks, it hits repeated `blocked`/`unknown` states, or the user asks. Retire = close its pane (only panes you created). A worker whose next task lies in another domain does NOT retire: it respawns under the same name with a fresh preamble and updated state card — a new session is the point, dropping now-worthless context; repo familiarity re-acquires from the environment in minutes. Fresh context is cheap because state lives in files.
- The pool stays at `MAX_WORKERS` or below; excess tasks wait in the queue.

## Worktrees

- Read-only roles (researcher, reviewer, planner) share the orchestrator's cwd.
- Each repo's own checkout is that repo's **base** — its integration point — even when it is itself a linked worktree of another checkout. Merges and verifications happen there. Single-repo work: the base is the orchestrator's cwd. Multi-repo work: one base per service repo, and the orchestrator's cwd is the workspace directory containing them.
- Concurrent editors each get **one git worktree** (herdr skill: worktree create) in the repo their task touches — pass that repo's checkout as `--cwd` — branch `swarm/<task-id>`, worktree directory named `<repo-name>--swarm-<task-id>` (in a multi-repo workspace many repos' worktrees share one directory and must stay distinguishable), with an explicit `--path` pointing at a **sibling of the source checkout** — outside every working tree. A relative path would nest the new worktree inside the current working tree and be swallowed by `git add .`. The worker's pane cwd sits at the worktree. Two workers on one branch never run at once.
- A task that must continue the base worktree's current branch runs **in place** there, serialized against any other in-place task; the base worktree counts as one worktree slot. Route a task here too when it is too small to amortize its own worktree — same-project parallelism pays off only when each parallel task outweighs the create/merge/remove overhead.
- Workspace-root files (compose files, workspace-level makefiles) live in no repo: edit them in place, serialized, like shared manifests — no worktree protection, never two tasks touching them at once.
- Merge each branch as soon as its task completes (see Scheduling step 3); run the brief's verification before marking the task integrated.
- **Worktrees are single-use.** Create at dispatch, from the base's current branch — which by then contains every merged dependency — and remove after integration (herdr skill: worktree remove). Never reuse a finished task's worktree for a later task: it is a pre-merge snapshot, and reusing it silently builds on stale code.

## Failure modes

- `agent_prompt_stalled` or timeout: inspect the worker before doing anything else. A half-applied prompt sent twice is worse than a late one.
- `unknown` state does not mean done. Verify via `result.md` (or a terminal read) before collecting.
- Worker died (pane shows a bare shell; a live pane whose pi footer is gone is the same signal): respawn under the same name and hand it the brief path again.
- Two retries failed on the same task: stop it, record it in the ledger, and surface it to the user. Fail loud.
- A worker reporting mid-task that the brief is far larger than triaged: accept its `DISPATCH-REQ` split or take the task back — never let it grind through repeated auto-compaction.

## Teardown

1. All tasks integrated and verified → close every worker pane **you created** (pane ids are in the ledger). Panes you did not create stay untouched.
2. Write `.herdr-swarm/report.md`: goal, task source, tasks run, outcomes, retirements, compactions, telemetry notes, unresolved items.
3. Tell the user where the report is. Keep `.herdr-swarm/` until the user confirms — it is the evidence trail.
