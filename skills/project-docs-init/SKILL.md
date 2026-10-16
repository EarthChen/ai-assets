---
name: project-docs-init
description: Initialize and maintain a project's AGENTS.md, CLAUDE.md, and README.md so they faithfully express the project's current state.
disable-model-invocation: true
argument-hint: "[--symlink] [--no-symlink]  whether to create CLAUDE.md→AGENTS.md symlink (default: on)"
---

Initialize and maintain a project's AGENTS.md (≤190 lines) and README.md so they faithfully express the **current state** of the codebase. CLAUDE.md is a symlink to AGENTS.md when the user opts in. Two situations, one process picked by file existence: files missing → **init**; files present → **maintain** against **drift** (what the docs claim vs what the code now is).

The root discipline: read facts from code, never invent them; ask the user only for intent the code cannot yield; surface every contradiction.

Report tags (used in the final report to the user): `[推论]` inferred, `[缺]` missing, `[待填]` README gap. `[推论]` and `[缺]` never appear in a file body; `[待填]` appears only in README.md.

## Probe

Before writing anything, read the codebase for the structural facts the docs stand on. Look each up in code. Fixed checklist, every run:

- Top-level tree (monorepo, single app, or library; which packages), package manager + lockfile, build / test / lint commands, language + runtime, git remote / default branch / submodules, CI, framework tells (config files, `Dockerfile`, `compose.yml`)
- **Dominant language** — read existing docs, code comments, recent commit messages; the generated AGENTS.md/README.md body follows this language (English-only project → English; Chinese → Chinese), not a fixed tongue
- Existing README/AGENTS content — intent reference, not a fact source
- Any project-specific manifest the tree reveals (e.g. `marketplace.json`, `third-party.json`) — read it; a missing manifest is how **drift** starts

**Completion criterion:** every probe item is resolved from code or routed: an unresolved structural fact → `[缺]` in the report (skip it in the files); an unresolved intent → Grill. No item asked of the user outside Grill.

## Cross-check

Before regenerating, hold the probed facts against the existing AGENTS.md and README.md, looking for **drift**: a statement in the docs the code contradicts, or a code fact the docs are silent on. When you find drift, **surface** it: list each contradiction to the user, ask which side is right, keep one, mark the other for cleanup. Code is often right; a doc can also record a decision the code hasn't caught up to — that's why you ask.

Statements in the existing docs with **no code corroboration** (team "don'ts", gotchas,踩坑经验, mechanism explanations like version-gating) are the highest-risk: they may be load-bearing knowledge the code can't reconstruct. Flag each one — "this statement has no code source; keep or delete?" — before touching it. It survives until the user answers.

A real `CLAUDE.md` file next to an `AGENTS.md` is a **conflict** (two source files); list it here too (see Symlink).

**Completion criterion:** every contradiction between docs and code, and every doc statement the code can't reproduce, is resolved (one side kept, the other marked) or listed to the user as unresolved.

## Destructive-change gate

Show a diff and wait for confirmation **only** when a change deletes or heavily rewrites existing content. Pure additions, dedup, and correcting obviously stale facts execute directly — the gate protects content the code can't rebuild. Treat a doubtful change as destructive and show the diff. In maintain mode, regenerating a file whole is destructive whenever the new body drops or rewrites existing statements: show the diff first.

## Generate

Regenerate each file whole, not as a patch. Match the dominant language from the probe. Before generating AGENTS.md, call the Skill tool with "writing-for-agents". README.md is human-facing; the section structure and constraints below apply to it.

### AGENTS.md — six sections, ≤190 lines hard

Aim well under 190.

| Section | Source |
| --- | --- |
| `## Project` (or project-language equivalent) — one-line what-it-is | factual + inferred (library/app/monorepo inferred from structure, listed as `[推论]` in the report; the positioning phrase, if you can't pin it, is a grill point) |
| `## Stack` — language, framework, DB, test runner | factual (manifests) |
| `## Commands` — build/test/lint, in code blocks | factual (scripts/Makefile/justfile) |
| `## Architecture` — what each key dir is for, no full tree | factual (tree) |
| `## Conventions` — falsifiable rules observable in code | inferred (read patterns from existing code: naming, export style, error handling; listed as `[推论]` in the report) |
| `## Rules` — don'ts / boundaries / security gotchas / PR & commit conventions | ask intent (team "never do X" is not in the code) |

AGENTS.md carries only finished statements. For a light intent item you can't resolve, infer it, write it untagged, and list it as `[推论]` in the report so the user can correct it in review; for a real boundary rule the code can't yield, grill.

After generating, run `wc -l AGENTS.md`. Over 190: tighten with no semantic loss, using the pruning levers from `writing-for-agents`. Still over: leave a `<!-- TODO: over 190 lines, trim X -->` marker and tell the user which section resists compression and what you'd cut, keeping every statement the code can't rebuild.

### README.md — six sections, no line cap, human-facing

| Section | Source |
| --- | --- |
| `# Title` + one-line summary | factual + `[待填]` (summary phrase if you can't pin it) |
| `## Features` / `## Purpose` | ask intent (selling points / philosophy aren't in code) |
| `## Installation` | factual (package manager + install command) |
| `## Quick Start` — minimal runnable example | factual + `[待填]` (the "smallest runnable scenario" may need confirming) |
| `## Usage` / API overview | factual (entry points, exports) |
| `## Documentation` / `## License` | `[待填]` for external doc links; license from `LICENSE` file |

`[待填]` placeholders are allowed here — gaps are visible and the reader expects to fill them. Collect all `[待填]` items in the final report for one-pass filling. Add `## Contributing` only when the user asks.

**Completion criterion (Generate):** `wc -l AGENTS.md` ≤ 190; README contains only `[待填]` gaps the code can't fill; both bodies match the dominant language; every `[推论]` / `[缺]` / `[待填]` item is listed in the report.

## Symlink

Handle CLAUDE.md per the argument (default `--symlink` on). Adaptive: whichever of AGENTS.md / CLAUDE.md already exists is the **source**, the missing one becomes a symlink to it.

| AGENTS.md | CLAUDE.md | `--symlink` (default) |
| --- | --- | --- |
| exists | missing | create `CLAUDE.md → AGENTS.md` |
| missing | exists | create `AGENTS.md → CLAUDE.md` |
| exists | symlink→AGENTS.md | no-op (correct state) |
| exists | real file | **conflict** (surfaced in Cross-check) — ask which to keep, migrate content, then link; a real CLAUDE.md is replaced only after that confirmation |
| missing | missing | after Generate creates AGENTS.md, create `CLAUDE.md → AGENTS.md` |

`--no-symlink`: maintain AGENTS.md/README.md only, never touch CLAUDE.md (existing symlink left as-is).

**Completion criterion:** CLAUDE.md's state matches the argument's intent; any real-file conflict was confirmed by the user.

## Grill

When you hit intent the code cannot yield — a positioning phrase you can't pin, a team boundary rule, a statement with no code corroboration — call the Skill tool with "grilling" for **these points only**. It carries the interview mechanics (design tree, frontier rounds, each question with your recommended answer). Scope the session to the unresolved intent points this run surfaced.

Grill fires for intent and for destructive changes (see the gate). Pure additions, dedup, and obviously stale facts need no question.

**Completion criterion:** every grill point either resolved by the user's answer, or left as a README `[待填]` or a `[推论]` report item, with the unresolved point named in the report.

## Verify

Re-run every Completion criterion above against the files as written, and confirm each destructive change was a diff the user confirmed. Report done only when all pass; name each failure in the report. "Done" means verified, not merely written.
