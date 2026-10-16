# Log Guide — the `log/` folder

The wiki's operation log is a **folder**, not a single file. One file per day, named `log/YYYYMMDD.md`. This keeps individual files small, makes daily activity easy to scan, and plays well with git diffs.

## File naming

- Filename: `log/YYYYMMDD.md` (e.g., `log/20260409.md`)
- Regex: `^\d{8}\.md$`
- No other files are allowed at the top of `log/`. `scripts/lint_wiki.py` will flag stray files.

## File format

```markdown
# 2026-04-09

## [09:15] ingest | google-gemma-4-article
- Source: raw/articles/google-gemma-4.md
- Touched: 5 wiki pages
  - summaries/google-gemma-4 (new)
  - concepts/Gemma.md (updated)
  - entities/Google.md (updated)
  - entities/Gemma 4.md (new)
  - index.md (updated)

## [14:30] audit | resolved 20260409-143022-a1b2
- Target: tech/Claude_Code.md
- Change: corrected file count from ~1,900 to ~1,800 per commit abc123
- Moved to: audit/resolved/20260409-143022-a1b2.md

## [15:05] lint | 2 dead links found, 2 fixed
- [[Claude Code Architecture]] → [[tech/claude-code/Claude_Code_Architecture]] in 2 files
```

Rules:
- One H1 per file, matching the filename date in ISO format (`YYYY-MM-DD`).
- One H2 per operation, starting with `## [HH:MM] <op> | <one-line description>`.
- Time is local time, 24h.
- Body is a short bullet list summarising what changed. Link to the files touched with wikilinks.

## Ops allowed in the log

`compile`, `ingest`, `query`, `promote` (output promoted to `wiki/concepts/`), `lint`, `audit`, `scaffold` (written by `scripts/scaffold.py`).

Entries are pointers: give the audit id plus a one-liner, not the audit body or article text. Put design rationale in `CLAUDE.md` "Notes for the LLM".
