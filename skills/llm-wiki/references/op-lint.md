# Operation: `lint`

Health check. Run:

```bash
uv run <skill-dir>/scripts/lint_wiki.py <wiki-root>
```

The script prints seven passes; exit code 1 means issues. For each issue, propose a fix, confirm with the user, then apply. Done when the script exits 0 or each remaining issue is named to the user.

Log: `## [HH:MM] lint | <N> issues found, <M> fixed`
