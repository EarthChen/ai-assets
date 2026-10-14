# Operation: `compile`

Scripts run as `uv run <skill-dir>/scripts/<name>.py`, where `<skill-dir>` is the directory containing SKILL.md. Every op appends one entry to `log/YYYYMMDD.md` ([log-guide.md](log-guide.md)).

(Re)structure wiki content from existing `raw/` material — including splitting oversized pages, merging near-duplicates, and rebuilding `index.md`.

**When to run**: after a big ingest batch, when an existing page has outgrown 1200 words, when `index.md` no longer reflects reality, or when the user says "clean up the wiki".

**Steps**:

1. Read `CLAUDE.md`, `wiki/index.md`, and every file in the target subtree.
2. For each page over ~1200 words: plan a split into `concepts/<topic>/` with an index + sub-pages. Confirm the plan with the user before writing.
3. For each pair of near-duplicate pages: propose a merge. Confirm, then rewrite.
4. Regenerate `wiki/index.md` so every page is listed exactly once.
5. Log: `## [HH:MM] compile | <what you did — files touched, splits, merges>`
