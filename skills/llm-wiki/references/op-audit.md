# Operation: `audit`

Process human feedback from `audit/`. File format and anchor lookup: [audit-guide.md](audit-guide.md).

**Steps**:

1. Run `uv run <skill-dir>/scripts/audit_review.py <wiki-root> --open` to get a grouped list. Process `error` and `warn` first, then `suggest`, then `info`.
2. For each open audit, read the file. Use the `anchor_before` / `anchor_text` / `anchor_after` window to locate the exact range in the target file (line numbers may have drifted).
3. Decide the action:
   - **Accept**: apply the correction to the target file in the smallest edit that fixes the issue, and bump its `updated:` field.
   - **Partially accept**: apply what makes sense, note the rest in the resolution.
   - **Reject**: explain why in the resolution — the feedback may be based on a misreading of scope or a contradictory source.
   - **Defer**: add the question to `CLAUDE.md` "Open research questions" with the audit id, and leave the audit in `audit/`.
4. For accepted, partial, and rejected audits, append a `# Resolution` section to the audit file:

   ```markdown
   # Resolution

   2026-04-10 · accepted.
   Fixed the file count (was "~1,900", corrected to "~1,800" per commit abc123).
   Updated: tech/Claude_Code.md lines 47–48.
   Log: [[log/20260410#1430 audit]]
   ```

   Format: date · decision (`accepted`, `partial`, `rejected`) on one line, then 1–3 sentences on what you did and why, the files touched, and a pointer to the log entry.
5. Set `status: resolved` in the audit file's frontmatter (`lint_wiki.py` requires `status` to equal the directory: `open` in `audit/`, `resolved` in `audit/resolved/`).
6. Move the file from `audit/` to `audit/resolved/`. Filename unchanged.
7. Log per resolved audit:

   ```
   ## [HH:MM] audit | resolved 20260409-143022-a1b2 — <one-line what>
   ```

Every audit ends in `resolved/` with its rationale, rejections included. Done when `audit_review.py --open` lists only deferred audits.
