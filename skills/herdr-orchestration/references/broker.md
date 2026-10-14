# Broker (worker-requested dispatch)

Workers never spawn. When a task outgrows one worker, the worker writes sub-briefs and requests dispatch; you stay the sole scheduler.

1. The worker writes `<swarm>/tasks/<parent-id>/<sub-id>.md` (hierarchical ids: T1a, T1b, …) and sends ONE line: `DISPATCH-REQ <sub-id> BLOCKED|PREFETCH`.
2. Review the sub-brief. **Reject** when it breaks scope rules or is too small to amortize a spawn (rule of thumb: under ~15 minutes of work stays with the requester) — state the reason; the requester may appeal once.
3. Approved: `BLOCKED` jumps the queue; `PREFETCH` ranks by normal priority. Dispatch to an idle same-domain worker first (reuse), else spawn under the pool cap.
4. Sub-workers report to **you** (single-scheduler invariant); you relay their `result.md` path to the requester as a one-line pointer.
5. When the requester's subtree completes, its sub-workers rejoin the domain pool by affinity or retire — never orphaned.
