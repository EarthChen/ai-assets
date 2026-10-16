# Operation: `ingest`

Add a new source. **One source typically touches 5–15 wiki pages.**

**Steps**:

1. Save source to the right subfolder:
   - web article → `raw/articles/<slug>.md`
   - paper → `raw/papers/<slug>.md` (extracted text for big PDFs)
   - note → `raw/notes/<slug>.md`
   - large binary (video, model weights, installer, dataset, PDF >10 MB) → do not copy; create the pointer file `raw/refs/<slug>.md`:

     ```yaml
     ---
     kind: ref
     external_path: /Volumes/external/models/llama-3-70b/
     size: ~140 GB
     ---
     ```

     followed by a short description of what it is and why it matters to this wiki. Wiki pages cite `[[raw/refs/<slug>]]` like any other source. This keeps the wiki repo git-friendly and portable.
2. Read the source in full.
3. Create `wiki/summaries/<slug>.md` (200–400 words — key takeaways, not a rewrite; see `references/article-guide.md`).
4. Create or update relevant concept pages in `wiki/concepts/`. If a concept page would exceed 1200 words, split instead of cramming.
5. Create or update entity pages in `wiki/entities/` for any new people / tools / papers / organizations referenced.
6. Update `wiki/index.md` so every new page appears once under the right category.
7. Log: `## [HH:MM] ingest | <slug> — <one-line description> (touched N pages)`
