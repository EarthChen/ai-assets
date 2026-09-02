---
name: ship-to-test
description: Ship each project's feature branch in a multi-project workspace to a test-environment branch — commit and push the feature branch, merge into the target branch (`test` by default), push it (triggers CI/CD), deploy changed inter-service artifacts at test-SNAPSHOT, switch back. Manual invocation.
disable-model-invocation: true
argument-hint: "[branch]  test-environment branch to merge into (default: test)"
---

# Ship to Test

Pushing the target branch triggers the test environment's CI/CD — the whole point of this workflow. Two consequences: the pushed pipeline is the only validator (no local checks, no watching the run — a project ends when its push and artifact deploy, if any, succeed), and a target branch with nothing new stays unpushed.

## Discovery

- Workspace root = current working directory.
- Projects = first-level subdirectories containing `.git` (repo or worktree); other subdirectories are skipped, nothing deeper is scanned.
- The workspace root being itself a git repository → single-project mode on it.
- Process projects sequentially, producers before consumers: order projects topologically by inter-project artifact dependencies (project A depends on project B when A's build manifest declares an artifact B publishes); unrelated projects keep discovery order.

## Guards

Run before any mutation. Each guard fails only its project (see **Failure & isolation**):

- No git repository, or no remote configured
- The current branch is the target branch itself
- A merge/rebase already in progress — an unfinished merge belongs to its owner
- The target branch checked out in another worktree — git allows one checkout per branch

## Service dependencies

An inter-service dependency is an artifact one workspace project publishes and another declares in its build manifest; it integrates through the remote artifact repository, never through git. Artifacts consumed only by services outside the workspace are out of scope — their versions belong to their owners.

- **Version** — both sides always read `test-SNAPSHOT`: the consumer's declaration and the producer's published version. When committing (step 1) or resolving a manifest conflict, rewrite any inter-project dependency declared at another version to `test-SNAPSHOT` and fold the fix into the commit.
- **Deploy** — the test environment resolves such an artifact from the remote repository, so a producer whose target branch moved in this ship must publish before its consumers ship (step 6).

## Per-Project Pipeline

The project's current branch is its feature branch; the **target branch** is the one named in the invocation argument (`test` when none is given). Every step ends on its stated criterion.

1. **Commit the working tree** — skip when the tree is already clean; otherwise analyze the diff and create conventional, atomic commits per the `git-workflow` skill (one concern per commit), committing directly, without confirmation. Done when the tree is clean.
2. **Push the feature branch** — add `-u` when upstream is missing. Rejected because the remote branch moved → **Feature-branch catch-up**. Done when the branch is on the remote.
3. **Switch to the target branch** — fetch, create a local target branch tracking `origin/<target>` when missing (remote has no target branch → fail the project), then sync the local target branch with its remote counterpart merge-style: the target is a shared branch, so it moves by merge only. Done when sitting on a target branch even with its remote counterpart.
4. **Merge the feature branch** — default merge commit, keeping full history on the shared branch. `Already up to date` → record "nothing to merge" and go to step 5. Conflicts → **Conflict resolution**. Done when the merge commit exists.
5. **Push the target branch** — done when the push succeeds.
6. **Deploy changed artifacts** — skip unless the project publishes an artifact consumed by a sibling project and its target branch moved during this ship (step 3 sync or step 4 merge). From the target branch, publish that artifact at `test-SNAPSHOT` using the project's own deploy command and version mechanism, skipping test execution (`mvn deploy -DskipTests` for Maven); in a multi-module project deploy the whole parent module from the project root rather than a single child module — the pipeline validates the code, deploy only publishes; verify the published version is `test-SNAPSHOT`, and if the project cannot publish at it, fail the project and hand off. One retry on transient failure. Done when the artifact is deployed at `test-SNAPSHOT`.
7. **Restore** — back on the feature branch, then the next project.

## Feature-branch catch-up

A feature push rejected as non-fast-forward means the remote feature branch moved — typically another worktree or a teammate pushed to it. A shared branch moves by merge only, same as the target:

1. **Integrate** — fetch, then merge `origin/<feature>` into the local feature branch. Conflicts → **Conflict resolution**. Done when the merge commit exists.
2. **Retry the push** — done when the push succeeds; rejected again → hand off per **Failure & isolation**.

## Conflict resolution

Resolve conflicts yourself by default; hand to the human only the hunks whose intent you cannot distinguish. Gate every conflicting hunk first:

- **Deterministic** — both sides' intent survives mechanically: pure additions with no semantic overlap (keep both), lockfile conflicts (regenerate with the package manager), one side a strict subset of the other (take the superset). Resolve these directly.
- **Ambiguous** — the sides are incompatible and a choice is required: present both sides' intent plus your suggested resolution, then wait for the human's decision. Anything not clearly deterministic is ambiguous.

For the resolution mechanics follow the `resolving-merge-conflicts` skill, with two overrides inside this workflow:

1. Human rejection ends the project: `git merge --abort`, fail the project. This replaces that skill's never-abort rule.
2. Skip its local-check step — the target branch's pipeline validates.

## Failure & isolation

- A remote rejection is a hand-off to the human: fail the project as-is — rebase, force-push, and retry stay the human's call. One exception recovers in-workflow: a feature push rejected because the remote branch moved goes through **Feature-branch catch-up** first.
- A deploy failure after a successful target push is a hand-off to the human: the target stays pushed, the project fails with reason "deploy failed", and every not-yet-shipped consumer is reported with a stale-artifact warning.
- Every failure path restores the project to a clean feature branch before moving on (`git merge --abort` + switch back when mid-merge). One project's failure stays inside that project.

## Final report

Per-project table: project, feature branch, commits created, merge result (merged / nothing to merge / failed with reason), target branch pushed or not, deploy result (`deployed <artifact>@test-SNAPSHOT` / skipped / failed).
