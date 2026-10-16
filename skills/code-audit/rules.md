# Code Audit Rules

Single source of truth for inline and dispatched execution. Read it in full before acting.

## Establish The Scope

1. Detect the review target:
   - A diff (`HEAD` vs a fixed point the user names) → all three sub-agents eligible.
   - A file, module, or arbitrary code range (no diff) → Lang+Lens runs alone; the Standards and Spec sub-agents are skipped (their process is diff-based — it cannot pin a fixed point without a diff).
2. Detect the language from extension, config files (`pom.xml`, `build.gradle`, `pyproject.toml`, `package.json`, `go.mod`), or explicit user statement. The Lens axis runs regardless of language. If no language is detectable and no diff exists, only the Lens axis runs.
3. Confirm the scope resolves before going further: `git rev-parse <fixed-point>` for a diff, or `test -f` for file targets. A bad ref or missing file fails here, not inside axis execution.

## Select Axes

Three sub-agents run independently. A change can pass one and fail the others; findings never merge or re-rank across axes.

**Sub-agent rule:** when you execute these rules as a sub-agent (for example the `code-reviewer` agent), spawn nothing: run the eligible axes sequentially in your own context, each with its own checklist and its own findings section, and keep the same aggregation rules.

- **Standards axis** (diff scope only) — does the code conform to documented repo standards plus a Fowler smell baseline? Prompt template comes from the mattpocock `code-review` skill's SKILL.md (located at install time — the path differs across harnesses and plugin caches).
- **Spec axis** (diff scope only) — does the code faithfully implement the originating issue/spec? Same prompt source.
- **Lang+Lens axis** — one sub-agent runs both checklists: the matching `references/<lang>-review.md` (language-specific traps: framework mismatches, async correctness, type-safety holes, query-plan killers) and `references/lens-review.md` (cross-language review lenses: silent failure, type design, security). Each finding tags its origin `[lang]` or `[lens]` so the aggregator can split reports.
- **Extra lang checklists** (run inside the Lang+Lens sub-agent in addition to `<lang>-review.md`): `references/fastapi-review.md` when the project depends on FastAPI; `references/database-review.md` when the target contains SQL or migration files.

## Execute

### Standards and Spec axes

Preparation happens in this session; the two sub-agents are plain workers. Locate the mattpocock `code-review` SKILL.md and read it (do not invoke it as a Skill tool — it is a process document, read for its prompt templates):

```bash
find -L "$PWD/skills" ~/.agents/skills ~/.pi/agent/skills ~/.claude/plugins/cache ~/.codex/plugins ~/.cursor/plugins -path '*/code-review/SKILL.md' -exec ls -t {} + 2>/dev/null | head -1
```

The newest file wins; empty output means the skill is not installed. Then, in this session:

1. The fixed point is already pinned (Establish The Scope) — reuse it.
2. Identify the spec source per code-review's Process step 2 (commit-message issue refs → user-supplied path → spec files under `docs/`, `specs/`, `.scratch/`). Nothing found → skip the Spec sub-agent and say so in the report.
3. Identify the standards sources per step 3 (`CODING_STANDARDS.md`, `CONTRIBUTING.md`, …) and take code-review's smell baseline from that step.

Spawn the Standards and Spec sub-agents in the same parallel batch as Lang+Lens, using code-review's step-4 prompt templates verbatim (diff command + commit list; standards-source list + the full smell baseline pasted in; spec path). Append the audit output record format below to both prompts so their findings aggregate cleanly. Baseline smells stay judgement calls; a documented repo standard overrides the baseline.

### Lang+Lens axis

Spawn one sub-agent for both checklists. Pass it the diff/file scope and the loaded reference files (read from this skill's directory first; the sub-agent has no other access): the matching `references/<lang>-review.md` if a language was detected, the extra lang checklists chosen in Select Axes, and `references/lens-review.md` always. The sub-agent applies both checklists top to bottom, classifies each finding, tags it `[lang]` or `[lens]`, and returns ranked findings records.

If the detected language has no reference file, the sub-agent runs only `references/lens-review.md` and reports "no lang checklist for <lang>".

Each finding carries a severity on the scale the reference checklists use: **CRITICAL**, **HIGH**, **MEDIUM**, or **LOW**. Output formats and approval verdicts (Approve/Warning/Block) inside a checklist do not apply; report with the record below.

State the evidence per finding: which rule fired, where in the diff or file, and why the severity holds.

## Aggregate

Present the reports under `## Standards`, `## Spec`, `## Lang (<language>)`, and `## Lens` headings, separately. (The Lang+Lens sub-agent returns findings tagged `[lang]` or `[lens]`; the aggregator splits them into the two headings by tag. The Standards and Spec sub-agents return their sections directly.) Do not merge or re-rank across axes. Where a Lens finding and a Lang finding flag the same code, note the overlap under both headings (do not dedupe). End with a one-line summary: total findings per axis and the worst issue within each axis.

Audit output uses this compact record per finding:

```plaintext
[axis / confidence / severity] finding
evidence: rule fired; location; public-API/compatibility impact of the fix
fix: exact change proposed
tradeoff: observable capability or behavior affected
verify: smallest decisive check
```

## Report

- **Done when** every axis that ran has its own section, every finding carries evidence and a `verify:` check, and each section ends with a worst-issue line (or "none").
- Keep a finding whose impact you cannot confirm, downgraded and labelled "unconfirmed".

## Apply

Fix mode only; audit mode stops at Report.

1. Apply only the findings the user selected from the report. Re-prove each against the current code first; drop it with reason when the proof fails.
2. One finding at a time: make the `fix:` change, then run the project's tests plus the finding's `verify:` check.
3. A failing check reverts that finding's own edit before the next finding starts. Never restore or checkout a whole file that holds other uncommitted changes — never discard unrelated user changes.
4. Report per finding: applied, reverted (with the failing check), or dropped (with the reason).
