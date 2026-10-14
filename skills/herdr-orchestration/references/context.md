# Context Telemetry

The compaction matrix and sequence live in SKILL.md: Context management. This file holds the telemetry pull script and the degradation chain.

**Telemetry — you pull, workers don't push.** Each kind renders context usage in its TUI footer in its own format (platforms.md: Telemetry). Read it with `herdr agent read <name> --source detection` and parse with the worker's kind pattern — inline this into the polling gate loop so it costs no LLM turns:

```bash
# pattern per worker kind — copy it from platforms.md: Telemetry; mixed pools
# look up each worker's kind in the ledger. pi pattern shown
for a in $watch; do
  ctx=$(herdr agent read "$a" --source detection --lines 15 2>/dev/null \
        | grep -oE 'ctx [0-9]+(\.[0-9]+)?%/[0-9]+[kKmM]?' | head -1)
  echo "$a: ${ctx:-ctx=?}"
done
```

**Telemetry degradation chain** (footer formats drift between agent versions, and per kind):

1. **Self-heal**: read the worker's `detection` output yourself, locate the context indicator in the rendered footer, derive the new pattern, and record it in the ledger header for the rest of this session.
2. **Heuristic fallback**: self-heal fails → record `ctx=unknown`, run the fallback heuristic, and notify the user **once** (`herdr notification show` + ledger notes + report.md). Never block the swarm on telemetry.
3. **Worker self-report escape hatch** (only on your explicit instruction): workers append `ctx=<totalTokens>` to their done/blocked line, read from their platform's session storage (platforms.md: Session JSONL) — the latest usage/`token_count` record, a storage-format source independent of the TUI.
