# Iterative Retrieval

Brief a subagent that needs codebase context you cannot predict upfront. Loop at most 3 cycles.

1. **Dispatch**: send a broad intent query (keywords, path globs) to an exploration subagent. Ask for candidate files, each with a one-line relevance reason.
2. **Evaluate**: grade each file high, related, or irrelevant for the task. Done when the high files cover every part the task touches and no gap is named.
3. **Refine**: add terminology found in the high files (the codebase may say "throttle" where the task said "rate limit"), exclude irrelevant paths, aim the next query at each named gap. Return to step 1.

After cycle 3, proceed with the best context found and list the remaining gaps in the brief. Pass file paths as context pointers, not file contents.
