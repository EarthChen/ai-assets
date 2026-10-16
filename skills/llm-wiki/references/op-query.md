# Operation: `query`

Answer a question **grounded in the wiki**, not general knowledge.

**Steps**:

1. Read `wiki/index.md`. List every page whose index line matches the question.
2. Read the listed pages in full; follow one level of wikilinks.
3. If the wiki lacks enough material, say so and suggest what to ingest next.
4. Synthesize the answer, citing pages inline with `[[Page Name]]`.
5. Save to `outputs/queries/<YYYY-MM-DD>-<question-slug>.md`.
6. If the answer is durable (a comparison, analysis, or new synthesis) → promote a cleaned-up version to `wiki/concepts/`, add to `index.md`.
7. Log: `## [HH:MM] query | <question-slug>` (and a separate `## [HH:MM] promote | ...` line if promoted).
