# Operation: `compile`

(Re)structure existing wiki content — splitting oversized pages, merging near-duplicates, and rebuilding `index.md`.

**Steps**:

1. Read `CLAUDE.md`, `wiki/index.md`, and every file in the target subtree.
2. For each page over 1200 words: plan a split into `concepts/<topic>/` with an index + sub-pages. Confirm the plan with the user before writing.
3. For each pair of near-duplicate pages: propose a merge. Confirm, then rewrite.
4. Regenerate `wiki/index.md` so every page is listed exactly once (`lint_wiki.py` "Missing index entries" must report none).
5. Log: `## [HH:MM] compile | <what you did — files touched, splits, merges>`
