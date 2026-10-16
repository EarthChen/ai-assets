# Tooling Tips

Optional setup notes for browsing the wiki. The skill ships three scripts (`scripts/scaffold.py`, `scripts/lint_wiki.py`, `scripts/audit_review.py`); everything below is human-side tooling.

## Obsidian setup

1. **Attachment folder**: Settings → Files and links → "Attachment folder path" → `raw/assets/` (Obsidian creates it on first download).
2. **New file location**: Settings → Files and links → "Default location for new notes" → `wiki/concepts/`.
3. **Download attachments hotkey**: Settings → Hotkeys → search "Download attachments" → bind to `Ctrl+Shift+D`. After clipping an article, hit the hotkey to download all images locally.
4. **Graph view** (`Ctrl+G`): an isolated node is an orphan page (`lint_wiki.py` flags these); a dense cluster is a sub-topic worth a folder-split under `wiki/concepts/`.

## Obsidian Web Clipper

1. Install from [obsidian.md/clipper](https://obsidian.md/clipper).
2. Configure the template to save to `raw/articles/`.
3. Clip an article → hit the download-images hotkey → file is ready for `ingest`.

For complex pages (paywalled, dynamic): copy-paste the main text manually, save as `raw/articles/<slug>.md`.

## Audit feedback UIs

An Obsidian plugin or a local web viewer can write `audit/*.md` files from a text selection. Neither ships with this skill; a human can also write the files by hand in the format of [audit-guide.md](audit-guide.md).
