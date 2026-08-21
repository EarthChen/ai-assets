# Code Audit Rules

Single source of truth for both inline and dispatched execution. Read end-to-end; never execute from memory.

## Establish The Scope

1. Detect the review target:
   - A diff (`HEAD` vs a fixed point the user names) → Standards+Spec, Lang, and Lens axes eligible.
   - A file, module, or arbitrary code range (no diff) → Lang and Lens axes run; the Standards+Spec axis is skipped (its process is diff-based — it cannot pin a fixed point without a diff).
2. Detect the language from extension, config files (`pom.xml`, `build.gradle`, `pyproject.toml`, `package.json`, `go.mod`), or explicit user statement. The Lens axis runs regardless of language. If no language is detectable and no diff exists, only the Lens axis runs.
3. Confirm the scope resolves before going further: `git rev-parse <fixed-point>` for a diff, or `test -f` for file targets. A bad ref or missing file fails here, not inside axis execution.

## Select Axes

Three axes run independently. A change can pass one and fail the others; they never merge or re-rank.

- **Standards+Spec axis** (diff scope only) — does the code conform to documented repo standards + a Fowler smell baseline, and does it faithfully implement the originating issue/spec? Process source: the mattpocock `code-review` skill's SKILL.md (located at install time — the path differs across harnesses and plugin caches).
- **Lang axis** — language-specific traps (framework mismatches, async correctness, type-safety holes, query-plan killers). Process source: `references/<lang>-review.md` in this skill's directory.
- **Lens axis** — cross-language review lenses: silent failure hunting, type design analysis, and security vulnerability detection. Pattern-level checks ("is this error silently swallowed?", "do these types make illegal states impossible?", "is this an OWASP Top 10 issue?"). Process source: `references/lens-review.md` in this skill's directory.

## Execute

### Standards+Spec axis

Locate the mattpocock `code-review` SKILL.md and follow its Process verbatim. Probe the standard install locations, preferring a path that resolves:

```bash
find -L "$PWD/skills" ~/.agents/skills ~/.pi/agent/skills ~/.claude/plugins/cache ~/.cursor/plugins -path '*code-review/SKILL.md' 2>/dev/null | head -1
```

If several hits remain (multiple cached plugin versions), prefer the newest. Read that SKILL.md and follow its Process (Pin the fixed point → Identify spec source → Identify standards sources → Spawn Standards and Spec sub-agents in parallel → Aggregate). Execute its steps; do not invoke it as a Skill tool — it is a process document, read and followed. Each finding cites the standard or spec line it violates; baseline smells are always judgement calls and a documented repo standard overrides the baseline.

### Lang axis

Spawn a lang sub-agent. Pass it the diff/file scope and the loaded `references/<lang>-review.md` checklist (read from this skill's directory first; the sub-agent has no other access). The sub-agent applies the checklist top to bottom, classifies each finding, and returns ranked findings records. Isolating the lang axis keeps the aggregator's context clean — the same reason the Standards and Spec axes run as sub-agents. If the detected language has no reference file, skip this axis and report "no lang checklist for <lang>".

Each finding classifies:

- **SAFE** — no dynamic references, no public-API or persisted-format impact.
- **CAREFUL** — reached via dynamic imports, string-based dispatch, or reflection.
- **RISKY** — part of a public API surface, persisted format, or compatibility path.

State the evidence per finding: which rule fired, where in the diff or file, and why the class holds.

### Lens axis

Spawn a lens sub-agent. Pass it the diff/file scope and the loaded `references/lens-review.md` checklist (read from this skill's directory first; the sub-agent has no other access). The sub-agent applies the three lenses (silent failure, type design, security) and returns ranked findings records. The Lens axis is orthogonal to the Lang axis: Lens asks pattern-level questions ("is this error swallowed?"); Lang asks language-specific rule questions ("is this Java catch written correctly?"). Both may fire on the same code — the aggregator flags overlaps, it does not dedupe by dropping findings.

## Aggregate

Present the axes under `## Standards+Spec`, `## Lang (<language>)`, and `## Lens` headings, separately. Do not merge or re-rank across axes. Where a Lens finding and a Lang finding flag the same code, note the overlap under both headings (do not dedupe). End with a one-line summary: total findings per axis and the worst issue within each axis.

Audit output uses this compact record per finding:

```plaintext
[axis / confidence / risk] finding
evidence: rule fired; location; dynamic/public/compatibility checks
fix: exact change proposed
tradeoff: observable capability or behavior affected
verify: smallest decisive check
```

## Report

- **Done when** every finding in scope has exited Execute proved or rejected with reason, and each axis has a worst-issue line (or "none").
- If applying (not audit-only), each approved finding passes one-change-at-a-time with a verify step that re-runs the smallest decisive check; revert on failure.
- Keep or downgrade a finding when dynamic reachability or compatibility cannot be ruled out. Never delete a finding the proof did not cover — report it as "kept, proof incomplete".
