# Simplification Rules

Execution rules for diff-scoped simplification. This file is the single source of truth: the `code-simplify` skill (inline) and the `code-simplifier` agent (dispatched) both execute it end-to-end. Do not execute from memory.

Two rules govern everything:

- **Behavior is invariant.** Inputs, outputs, side effects, error behavior, and edge cases stay unchanged. If a change might alter behavior, it is not a simplification. Existing tests of surviving behavior pass without modification; when you delete code, the tests that exist only for it go with it — tests are evidence, not disposable line count.
- **The scope list is a fence.** Edit only files inside the scope. Report adjacent mess; don't fix it.

## Establish The Scope

Use the scope the user names. Unspecified: uncommitted changes if any exist, else the last commit.

| Scope | Diff |
| --- | --- |
| Uncommitted changes | `git diff HEAD` (staged + unstaged) plus untracked files from `git status` — new files are part of the scope |
| Recent commit(s) | `git diff HEAD~N..HEAD`, or the commit/range the user names |
| PR / MR (full branch) | `git fetch origin <base> && git diff origin/<base>...HEAD` |

For a PR/MR, `<base>` is the merge target (`main`, `master`, or the MR's target branch); the three-dot form shows only what this branch adds. If the branch is stale, sync base first — otherwise base drift pollutes the diff.

Then:

1. List the changed files; that list is the working scope. Drop generated, vendored, and lockfile paths from it.
2. Preserve unrelated uncommitted work — never discard or fold in changes outside the scope.
3. Read repo conventions (`AGENTS.md` / `CLAUDE.md` / rules). Simplification means moving toward the codebase's style, not imposing an external one.
4. Find the repo's test/lint/build commands and run a proportional baseline when feasible. A red baseline limits what later checks can prove; record it instead of claiming a regression.

## Understand Before Touching

Chesterton's Fence: before changing or removing anything, know why it exists.

For each changed region answer: what is its responsibility? What calls it, what does it call? What are the edge cases and error paths? Do tests define its behavior? Why might it be written this way — performance, platform constraint, history? Check `git log` / `git blame`.

A region you cannot explain is a region you do not simplify — read more context first.

## Scan

Walk the diff against every section below; collect findings with a one-line rationale each and rank by comprehension gain per risk. Finding nothing to change is a valid result — report it and stop.

### Names

Variable names, function names, and comments are all prose. Apply Orwell's rules ("Politics and the English Language"):

> Never use a long word where a short one will do.
>
> If it is possible to cut a word out, always cut it out.
>
> Never use the passive where you can use the active.
>
> Never use a foreign phrase, a scientific word, or a jargon word if you can think of an everyday English equivalent.

Latinate vocabulary (reconcile, coalesce, normalize) sounds technical and abstract; Anglo-Saxon words (prune, run, watch, stop, drop) are short and physical. Prefer the Saxon word.

1. **One word per concept, one concept per word.** If `sync` names "pulling remote changes," it cannot also name "flushing edits to disk;" rename one of them.
2. **Cut words the context already carries.** A module named `workspaceWatcher` does not need `startNativeWorkspaceWatcher`; `watchWorkspace` says the same thing.
3. **A compound name is usually a hedge:** ❌ `lastObservedDiskContent` is a specification to defend; ✅ `baseline` is a readable description.
4. **Generic names describe nothing.** `data`, `result`, `temp`, `val` → name the content: `userProfile`, `validationErrors`.
5. **Use full words unless the abbreviation is universal** (`id`, `url`, `api`): `usr`, `cfg`, `btn` → `user`, `config`, `button`.
6. **Names must match behavior.** A function named `get` that also mutates is a lie — rename to reflect what it actually does.

### Comments

State, in plain English, the constraint the code cannot show: why the **non-obvious** exists.

- ✅ If code is complex and the implementation is non-obvious, add a comment.
- ✅ If a function contains complex behaviors or side effects, add a doc comment.
- ✅ Keep why-comments the code cannot carry: `// Retry because the API is flaky`.
- 🗑️ If a comment narrates change history from the conversation, delete it.
- 🗑️ If a comment restates code whose behavior is self-evident (`// increment counter` above `count++`), delete it.

### Structure

1. **Inverted pyramid.** Within a file, lead with the exported or significant functions and push helpers below them. Don't bury the lead.
2. **Related concepts over monoliths.** Break a large file into modules that each own one concept.
3. **Combine overlapping concepts.** If two types, functions, or constants overlap significantly, merge them. The fewer distinct concepts a reader must hold in their head, the better.
4. **Use shared code.** Common utilities (ex. file path parsing) may exist in the codebase already. Check for library or utility functions before inlining.
5. **Derivability.** If a value can be computed from values already in scope, don't pass or store it separately. Removing derivable state often simplifies signatures, types, and control flow in one move. Example: an `isDirty` parameter that is always `editorContent !== baseline` can be dropped.
6. **Deep nesting (3+ levels)** → extract conditions into guard clauses or a well-named helper.
7. **Long functions (50+ lines, multiple responsibilities)** → split into focused functions with descriptive names.
8. **Nested ternaries** → `if/else` chains, `switch`, or lookup maps.
9. **Boolean parameter flags** (`doThing(true, false, true)`) → options object or separate functions.
10. **Repeated conditionals** (same check in multiple places) → extract to a well-named predicate function.

### Redundancy

Deletion needs proof, not a hunch:

1. Search the whole repo for the symbol, its file path, string/event/config name, and alternate call syntax.
2. Classify every hit: **production** (runtime source, shipped config, real entrypoints, migrations) vs **non-production** (tests, docs, comments) vs **ambiguous** (reflection, registries, lazy imports, plugins, serialization, externally consumed exports — inspect before classifying).
3. Delete only when no production consumer remains and dynamic reachability is ruled out. Otherwise keep or downgrade the finding.

Findings to look for:

- **Duplicated logic** — same 5+ lines in multiple places → extract to a shared function.
- **Dead code in the changed region** — unreachable branches, unused vars, commented-out blocks → prove dead, remove.
- **Unnecessary abstraction** — a wrapper that adds no value → inline; call the underlying function directly.
- **Over-engineering** — factory-for-a-factory, strategy-with-one-strategy → replace with the direct approach.
- **Redundant type assertions** — casting to a type already inferred → remove.
- **Mirrored fact** — two caches, summaries, or state stores recording the same truth → collapse onto the load-bearing representation; never replace two truths with a synchronization wrapper.
- **Speculative generality** — unset knobs, fixed feature flags, unused fallbacks, one-implementation interfaces → remove.
- **Lifecycle duplication** — several flags, sentinels, or promises representing one transition (ready, stopped, flushed) → collapse onto one owner.
- **Misplaced defense** — copies, freezes, or validators guarding a same-process typed handoff rather than a real trust boundary → remove.
- **Hand-rolled infrastructure** — local parsers, retry loops, globbing, diffing already covered by the standard library or an installed dependency → replace.
- **Added-then-abandoned residue** — the implementation disappeared but flags, schemas, docs, tests, or compatibility branches still describe it → remove the residue.

Do not confuse duplication with necessary independence: separate backends, adapters, or representations may intentionally test a contract or protect distinct owners.

### Overfitting

Code must stand on its own. If a change only makes sense to someone who watched it happen (this conversation, this PR), it is overfitted. Write for the reader who arrives with no history.

- If a name or comment needs the conversation to be understood, rewrite it against the codebase's own vocabulary.
- **No backwards compatibility with unshipped code.** Supporting an old signature, alias, or data shape that only existed earlier in the same branch is compatibility with something that was never deployed. Delete the old path and update its callers.

### Do Not Simplify Away

- validation at trust boundaries
- authorization and security controls
- accessibility basics
- data-loss prevention
- durable-data and wire-format compatibility
- cleanup that establishes resource quiescence

## Apply

1. One simplification at a time; never batch untested changes — a failure must point at one cause.
2. Before deleting anything, prove it dead per the Redundancy section: search consumers across the whole repo, rule out dynamic reachability. When in doubt, keep it.
3. Prefer clarity over cleverness: explicit code beats compact code that needs a mental pause to parse.
4. Keep balance: don't inline a helper that gave a concept a name, don't merge unrelated logic into one complex function, don't strip abstractions that exist for testability. Fewer lines is not the goal; easier comprehension is.
5. **Rule of 500:** if a pass would touch more than 500 lines, stop and hand off — manual edits at that scale are error-prone and exhausting to review.
6. Already-committed code gets its own simplification commits; uncommitted polish folds into the pending changes.

Done when every ranked finding is applied, deferred with reason, or rejected — nothing silently dropped.

## Verify

1. Run the narrowest tests covering the changed files, then the repo's relevant lint/type/test/build gates.
2. Re-search deleted symbols and strings for stale references.
3. Inspect the full diff: no scope creep, no weakened error handling, no behavior change.
4. If a check fails, revert that change or repair the proof. Never weaken a meaningful check to force a simplification through.

Tests that must be modified to pass are a red flag — you likely changed behavior.

## Report

- what was simplified and why (one line each);
- findings intentionally skipped and why;
- exact verification run and result;
- adjacent problems outside the scope worth a follow-up;
- the path this rules file was loaded from.

Audit findings carry: the proposed change, the evidence it is safe (consumers searched, dynamic reachability ruled out), the smallest decisive check, and estimated net reduction.

Do not claim safety from green tests alone, and do not claim value from deletion volume alone.
