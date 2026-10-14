# Operation: `audit`

Scripts run as `uv run <skill-dir>/scripts/<name>.py`, where `<skill-dir>` is the directory containing SKILL.md. Every op appends one entry to `log/YYYYMMDD.md` ([log-guide.md](log-guide.md)).

Process human feedback from `audit/`.

**Steps**:

1. Run `uv run <skill-dir>/scripts/audit_review.py <wiki-root> --open` to get a grouped list.
2. For each open audit, read the file. Use the `anchor_before` / `anchor_text` / `anchor_after` window to locate the exact range in the target file (line numbers may have drifted).
3. Decide the action:
   - **Accept**: apply the correction to the target file.
   - **Partially accept**: apply what makes sense, note the rest in the resolution.
   - **Reject**: explain why in the resolution — the feedback may be based on a misreading of scope or a contradictory source.
   - **Defer**: add to `CLAUDE.md` "Open research questions" and leave the audit in place with a comment.
4. For applied audits, append a `# Resolution` section to the audit file:

   ```markdown
   # Resolution

   2026-04-10 · accepted.
   Fixed the file count (was "~1,900", corrected to "~1,800" per commit abc123).
   Updated: tech/Claude_Code.md lines 47–48.
   ```

5. Move the file from `audit/` to `audit/resolved/`. Filename unchanged.
6. Log per resolved audit:

   ```
   ## [HH:MM] audit | resolved 20260409-143022-a1b2 — <one-line what>
   ```

7. Never delete audit files. Rejected ones still go to `resolved/` with the rejection rationale in their resolution section — that's valuable history.

See `references/audit-guide.md` for the full audit file format.
