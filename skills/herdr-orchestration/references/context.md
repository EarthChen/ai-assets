# Context Telemetry and Polling Gate

The compaction matrix and sequence live in SKILL.md: Context management. This file holds the polling gate script (with the telemetry pull inlined, so it costs no LLM turns) and the degradation chain.

Adapt the script to the live CLI. Telemetry pattern per worker kind: platforms.md: Telemetry (look up each worker's kind in the ledger in a mixed pool; the pi pattern is shown).

```bash
watch="pay-wk-frontend pay-wk-backend pay-wk-payments"
deadline=$(( $(date +%s) + 1800 ))   # 30 min backstop (SKILL.md: Scheduling, step 5)
while :; do
  settled=$(herdr agent list | jq -r --arg w "$watch" '
    ($w | split(" ")) as $names
    | .result.agents[]
    | select((.agent as $a | $names | index($a))
        and (.agent_status=="idle" or .agent_status=="done" or .agent_status=="blocked" or .agent_status=="unknown"))
    | "\(.agent) \(.agent_status)"')
  [ -n "$settled" ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { settled="TIMEOUT"; break; }
  sleep 20
done
echo "$settled"
for a in $watch; do   # telemetry: read each worker's footer once the gate returns
  ctx=$(herdr agent read "$a" --source detection --lines 15 2>/dev/null \
        | grep -oE 'ctx [0-9]+(\.[0-9]+)?%/[0-9]+[kKmM]?' | head -1)
  echo "$a: ${ctx:-ctx=?}"
done
```

**Telemetry degradation chain** (footer formats drift between agent versions, and per kind):

1. **Self-heal**: read the worker's `detection` output yourself, locate the context indicator in the rendered footer, derive the new pattern, and record it in the ledger header for the rest of this session.
2. **Heuristic fallback**: self-heal fails → record `ctx=unknown`, run the fallback heuristic, and notify the user **once** (`herdr notification show` + ledger notes + report.md). Never block the swarm on telemetry.
3. **Worker self-report escape hatch** (only on your explicit instruction): workers append `ctx=<totalTokens>` to their done/blocked line, read from their platform's session storage (platforms.md: Session JSONL) — the latest usage/`token_count` record, a storage-format source independent of the TUI.
