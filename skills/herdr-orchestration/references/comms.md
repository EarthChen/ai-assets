# Communication Protocol

Two planes: **control** (short, direct herdr prompts) and **data** (files under `.herdr-swarm/`, messages carry paths). This file specifies the etiquette; the herdr skill owns every command.

## State etiquette (mandatory before any prompt)

Check the target's state first (herdr skill: agent get).

| Target state | Action |
| --- | --- |
| `idle` | Prompt directly. |
| `working` | Never prompt. Drop a file into `<swarm>/inbox/<name>/`; the recipient clears its inbox at task boundaries. |
| `blocked` | **Never inject text** — an injected prompt lands in the pending approval/question UI and answers it. Inspect (agent get/read), then unblock with the right key/answer yourself, or escalate. |
| `unknown` | Treat as working. Verify before acting. |

If a target started working between your check and your send, verify with it before resending — a half-applied prompt sent twice is worse than a late one.

## Inbox

- Path: `<swarm>/inbox/<recipient>/<sender>-<topic>.md`.
- The recipient clears its inbox at every task boundary (worker contract: roles.md).
- If the target is idle and the message short, a direct prompt is simpler than an inbox drop — etiquette decides, not habit.

## Orchestrator ↔ worker

- Assignments, answers, status: direct prompts (idle only) — one line to a few lines.
- A worker's completion is ONE line: `"<task-id> done: <swarm>/tasks/<task-id>/result.md"` or `"<task-id> blocked: <reason>"`. Workers append `ctx=<totalTokens>` only when the orchestrator has instructed self-reporting (telemetry escape hatch).
- Brokered dispatch: `DISPATCH-REQ <sub-id> BLOCKED|PREFETCH` (protocol in SKILL.md § Broker).

## Worker ↔ worker (peers)

Allowed across a shared contract boundary only: two briefs referencing the same `<swarm>/contracts/<name>.md` make those workers automatic peers, and you name them in each other's preamble. Ad-hoc peer links go through you: you announce the link to both sides. Topic limit, round cap (`PEER_ROUND_CAP`), and audit rules live in the worker contract (roles.md: Common contract); state etiquette above applies to peers too.

## Topology diagram

```mermaid
flowchart TB
  O["Orchestrator — sole scheduler & integrator"]
  subgraph pool["worker pool (≤ MAX_WORKERS)"]
    W1["pay-wk-frontend"]
    W2["pay-wk-backend"]
    W4["pay-wk-payments"]
    W3["pay-wk-reviewer (aux)"]
  end
  FS[(".herdr-swarm/&lt;plan-id&gt;/<br/>plan · ledger · tasks<br/>contracts · state · inbox")]
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

Worker names here are illustrative — the pool may be homogeneous (e.g. all backend: `pay-wk-payments`, `pay-wk-auth`, `pay-wk-orders`). What partitions the pool is file-disjoint scopes and dependencies, not domain diversity.
