# Operation: `ingest`

Scripts run as `uv run <skill-dir>/scripts/<name>.py`, where `<skill-dir>` is the directory containing SKILL.md. Every op appends one entry to `log/YYYYMMDD.md` ([log-guide.md](log-guide.md)).

Add a new source. **One source typically touches 5–15 wiki pages.**

**Steps**:

1. Save source to the right subfolder:
   - web article → `raw/articles/<slug>.md`
   - paper → `raw/papers/<slug>.md` (extracted text for big PDFs)
   - note → `raw/notes/<slug>.md`
   - large binary → `raw/refs/<slug>.md` pointer file (see raw file policy)
2. Read the source in full.
3. Create `wiki/summaries/<slug>.md` (200–400 words — key takeaways, not a rewrite; see `references/article-guide.md`).
4. Create or update relevant concept pages in `wiki/concepts/`. Respect divide-and-conquer: if a concept page would exceed 1200 words, split instead of cramming.
5. Create or update entity pages in `wiki/entities/` for any new people / tools / papers / organizations referenced.
6. Update `wiki/index.md` so the new pages appear under the right category.
7. Log: `## [HH:MM] ingest | <slug> — <one-line description> (touched N pages)`
