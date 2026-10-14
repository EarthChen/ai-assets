# Operation: `lint`

Scripts run as `uv run <skill-dir>/scripts/<name>.py`, where `<skill-dir>` is the directory containing SKILL.md. Every op appends one entry to `log/YYYYMMDD.md` ([log-guide.md](log-guide.md)).

Health check. Run:

```bash
uv run <skill-dir>/scripts/lint_wiki.py <wiki-root>
```

The script reports:

- **Dead wikilinks** — `[[Target]]` where `Target.md` doesn't exist
- **Orphan pages** — pages with no inbound wikilinks
- **Missing index entries** — pages not listed in `wiki/index.md`
- **Frequently-linked missing pages** — `[[X]]` referenced 3+ times but no page
- **log/ shape** — stray files or wrong filenames in `log/`
- **audit/ shape** — malformed YAML frontmatter in `audit/*.md`
- **Audit target resolution** — every open audit's `target` file must exist

For each issue, propose a fix, confirm with the user, then apply. Log: `## [HH:MM] lint | <N> issues found, <M> fixed`.
