# Operation: `query`

Scripts run as `uv run <skill-dir>/scripts/<name>.py`, where `<skill-dir>` is the directory containing SKILL.md. Every op appends one entry to `log/YYYYMMDD.md` ([log-guide.md](log-guide.md)).

Answer a question **grounded in the wiki**, not general knowledge.

**Steps**:

1. Read `wiki/index.md`. Scan for relevant pages by category.
2. Read the identified pages in full; follow one level of wikilinks.
3. If the wiki doesn't have enough material, say so and suggest what to ingest next instead of making something up.
4. Synthesize the answer, citing pages inline with `[[Page Name]]`.
5. Save to `outputs/queries/<YYYY-MM-DD>-<question-slug>.md`.
6. If the answer is durable (a comparison, analysis, or new synthesis) → promote a cleaned-up version to `wiki/concepts/`, add to `index.md`.
7. Log: `## [HH:MM] query | <question-slug>` (and a separate `## [HH:MM] promote | ...` line if promoted).
