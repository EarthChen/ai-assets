---
name: project-docs-init
description: Initialize and maintain a project's AGENTS.md, CLAUDE.md, and README.md so they faithfully express the project's current state.
disable-model-invocation: true
argument-hint: "[--symlink] [--no-symlink]  whether to create CLAUDE.md→AGENTS.md symlink (default: on)"
---

Initialize and maintain a project's AGENTS.md (≤190 lines) and README.md so they faithfully express the **current state** of the codebase. CLAUDE.md is a symlink to AGENTS.md when the user opts in. Two situations, one process picked by file existence: files missing → **init**; files present → **maintain** against **drift** (what the docs claim vs what the code now is).

The root discipline: read facts from code, never invent them; ask the user only for intent the code cannot yield; surface contradiction rather than paper over it.

## Probe

Before writing anything, read the codebase for structural facts — the factual base the docs stand on. Do not ask the user for any of these; look them up. Fixed checklist, every run:

- Top-level tree — monorepo, single app, or library; which packages
- Package manager + lockfile — `uv.lock`, `pnpm-lock.yaml`, `package-lock.json`, `Cargo.lock`, `go.mod`, …
- Build / test / lint commands — `package.json` scripts, `pyproject.toml [tool.*]`, `Makefile`, `justfile`
- Language + runtime — `requires-python`, `.node-version`, `rust-toolchain`, `go.mod`
- Git — remote, default branch, submodules
- CI — `.github/workflows`, `.gitlab-ci.yml`
- Framework tells — `next.config`, `vite.config`, Spring config, `Dockerfile`, `compose.yml`
- **Dominant language** — read existing docs, code comments, recent commit messages; the generated AGENTS.md/README.md body follows this language (English-only project → English; Chinese → Chinese), not a fixed tongue
- Existing README/AGENTS content — intent reference, not a fact source
- Any project-specific manifest the tree reveals (e.g. `marketplace.json`, `third-party.json`) — read it; missing such a file is how **drift** starts

**Completion criterion:** every probe item either resolved from code or marked `[缺]` (missing — skip, do not guess). No item asked of the user.

A probe item the code cannot resolve is not your cue to invent — it becomes a **grill** point (see below).

## Cross-check

Before regenerating, hold the probed facts against the existing AGENTS.md and README.md, looking for **drift**: a statement in the docs the code contradicts, or a code fact the docs are silent on. When you find drift, **surface** it — do not silently overwrite, do not average the two into a mush. List each contradiction to the user: which side is right, keep one, mark the other for cleanup. Code is often right; but a doc can record a decision the code hasn't caught up to — that's why you ask, not assume.

Statements in the existing docs with **no code corroboration** (team "don'ts", gotchas,踩坑经验, mechanism explanations like version-gating) are the highest-risk: they may be load-bearing knowledge the code can't reconstruct. Flag these explicitly — "this statement has no code source; keep or delete?" — before touching them. Never silently drop them.

**Completion criterion:** every contradiction between docs and code is either resolved (one side kept, the other marked) or listed to the user as unresolved. No silent overwrite of a doc statement the code can't reproduce.

## Generate

Regenerate each file whole — not a patch. Match the dominant language from the probe.

### AGENTS.md — six sections, ≤190 lines hard

Tight by design: every line loads into the agent's context on every session. Aim well under 190; 190 is the wall.

| Section | Source |
|---|---|
| `## Project` (or project-language equivalent) — one-line what-it-is | factual + `[推断]` (library/app/monorepo inferred from structure; the positioning phrase, if you can't pin it, is a grill point) |
| `## Stack` — language, framework, DB, test runner | factual (manifests) |
| `## Commands` — build/test/lint, in code blocks | factual (scripts/Makefile/justfile) |
| `## Architecture` — what each key dir is for, no full tree | factual (tree) |
| `## Conventions` — falsifiable rules observable in code | `[推断]` (read patterns from existing code: naming, export style, error handling) |
| `## Rules` — don'ts / boundaries / security gotchas / PR & commit conventions | ask intent (team "never do X" is not in the code) |

No `[待填]` placeholders in AGENTS.md — they cost lines and the agent reads them as incomplete. For a light intent item you can't resolve, infer it and tag `[推断]` so the user can correct in review; for a real boundary rule the code can't yield, grill.

After generating, count lines. Over 190: **self-tighten** with no semantic loss first — dedupe adjacent bullets, collapse repeated phrasing, drop redundant examples. Still over: leave a `<!-- TODO: over 190 lines, trim X -->` marker and tell the user which section resists compression and what you'd cut. Do not silently truncate mid-sentence; do not silently axe content the code can't rebuild.

### README.md — six sections, no line cap, human-facing

| Section | Source |
|---|---|
| `# Title` + one-line summary | factual + `[待填]` (summary phrase if you can't pin it) |
| `## Features` / `## Purpose` | ask intent (selling points / philosophy aren't in code) |
| `## Installation` | factual (package manager + install command) |
| `## Quick Start` — minimal runnable example | factual + `[待填]` (the "smallest runnable scenario" may need confirming) |
| `## Usage` / API overview | factual (entry points, exports) |
| `## Documentation` / `## License` | `[待填]` for external doc links; license from `LICENSE` file |

`[待填]` placeholders are allowed here — README is human-facing, gaps are visible and the reader expects to fill them. Collect all `[待填]` items and list them in the final report for one-pass filling; do not grill the user per-placeholder.

No `## Contributing` section unless the user asks.

**Completion criterion:** AGENTS.md ≤190 lines (counted); README contains only `[待填]` gaps the code genuinely can't fill; both bodies match the dominant language; every `[推断]` / `[缺]` tag is present for the user to review.

## Symlink

Handle CLAUDE.md per the argument (default `--symlink` on). Adaptive: whichever of AGENTS.md / CLAUDE.md already exists is the **source**, the missing one becomes a symlink to it.

| AGENTS.md | CLAUDE.md | `--symlink` (default) |
|---|---|---|
| exists | missing | create `CLAUDE.md → AGENTS.md` |
| missing | exists | create `AGENTS.md → CLAUDE.md` |
| exists | symlink→AGENTS.md | no-op (correct state) |
| exists | real file | **conflict** — two source files; surface per Cross-check, ask which to keep, migrate content, then link. Never silently overwrite a real CLAUDE.md |
| missing | missing | after Generate creates AGENTS.md, create `CLAUDE.md → AGENTS.md` |

`--no-symlink`: maintain AGENTS.md/README.md only, never touch CLAUDE.md (existing symlink left as-is).

**Completion criterion:** CLAUDE.md's state matches the argument's intent; any real-file conflict was surfaced and confirmed, not silently overwritten.

## Grill

When you hit intent the code cannot yield — a positioning phrase you can't pin, a team boundary rule, a statement with no code corroboration — stop and grill the user: **one question at a time**, each with your recommended answer, wait for the reply before the next. This is not a bulk Q&A; one-at-a-time avoids bewilderment.

Only grill on what the code can't resolve. Everything probed from code (structure, commands, stack, language) never becomes a question — you already have the answer. The grill fires for intent and for destructive changes (deleting or heavily rewriting existing content) — never for pure additions, dedup, or correcting obviously stale facts, which you do directly.

**Completion criterion:** every grill point either resolved by the user's answer, or left as a `[待填]`/`[推断]`/TODO marker with the unresolved point named in the report. No intent fabricated to fill a gap.

## Verify

Before reporting done, run this checklist. All green → report complete. Any red → name it in the report, do not claim done.

- [ ] AGENTS.md ≤190 lines (counted this run)
- [ ] CLAUDE.md state matches the symlink argument (or conflict was surfaced+confirmed)
- [ ] Cross-check leaves no unresolved doc-vs-code contradiction (every drift surfaced, none silently overwritten)
- [ ] Every `[推断]` / `[缺]` / `[待填]` marker listed in the report for the user to review
- [ ] Every grill point resolved or explicitly left as a named TODO
- [ ] Any destructive change (delete / heavy rewrite) shown as a diff the user confirmed
- [ ] Both file bodies follow the project's dominant language

**Completion criterion:** every checkbox green, or every red item named in the report with no failure hidden. "Done" means verified, not merely written.

## Destructive-change gate

A diff is shown and confirmation waited for **only** when a change deletes or heavily rewrites existing content. Pure additions, dedup, and correcting obviously stale facts execute directly — the gate exists to protect content the code can't rebuild, not to slow routine maintenance. When in doubt whether a change is destructive, treat it as destructive and show the diff.
