---
name: ship-to-test
description: Ship each project's feature branch in a multi-project workspace to a test-environment branch — commit and push the feature branch, merge into the target branch (`test` by default), push it (triggers CI/CD), switch back. Manual invocation.
disable-model-invocation: true
argument-hint: "[branch]  test-environment branch to merge into (default: test)"
---

# Ship to Test

Pushing the target branch triggers the test environment's CI/CD — the whole point of this workflow. Two consequences: the pushed pipeline is the only validator (no local checks, no watching the run — a project ends when its push succeeds), and a target branch with nothing new stays unpushed.

## Discovery

- Workspace root = current working directory.
- Projects = first-level subdirectories containing `.git` (repo or worktree); other subdirectories are skipped, nothing deeper is scanned.
- The workspace root being itself a git repository → single-project mode on it.
- Process projects sequentially.

## Guards

Run before any mutation. Each guard fails only its project (see **Failure & isolation**):

- No git repository, or no remote configured
- The current branch is the target branch itself
- A merge/rebase already in progress — an unfinished merge belongs to its owner
- The target branch checked out in another worktree — git allows one checkout per branch

## Per-Project Pipeline

The project's current branch is its feature branch; the **target branch** is the one named in the invocation argument (`test` when none is given). Every step ends on its stated criterion.

1. **Commit the working tree** — skip when the tree is already clean; otherwise analyze the diff and create conventional, atomic commits per the `git-workflow` skill (one concern per commit), committing directly, without confirmation. Done when the tree is clean.
2. **Push the feature branch** — add `-u` when upstream is missing. Done when the branch is on the remote.
3. **Switch to the target branch** — fetch, create a local target branch tracking `origin/<target>` when missing (remote has no target branch → fail the project), then sync the local target branch with its remote counterpart merge-style: the target is a shared branch, so it moves by merge only. Done when sitting on a target branch even with its remote counterpart.
4. **Merge the feature branch** — default merge commit, keeping full history on the shared branch. `Already up to date` → record "nothing to merge" and go to step 6. Conflicts → **Conflict resolution**. Done when the merge commit exists.
5. **Push the target branch** — done when the push succeeds; that ends the project.
6. **Restore** — back on the feature branch, then the next project.

## Conflict resolution

Gate every conflicting hunk first:

- **Deterministic** — both sides' intent survives mechanically: pure additions with no semantic overlap (keep both), lockfile conflicts (regenerate with the package manager), one side a strict subset of the other (take the superset). Resolve these directly.
- **Ambiguous** — the sides are incompatible and a choice is required: present both sides' intent plus your suggested resolution, then wait for the human's decision. Anything not clearly deterministic is ambiguous.

For the resolution mechanics follow the `resolving-merge-conflicts` skill, with two overrides inside this workflow:

1. Human rejection ends the project: `git merge --abort`, fail the project. This replaces that skill's never-abort rule.
2. Skip its local-check step — the target branch's pipeline validates.

## Failure & isolation

- A remote rejection (feature push or target-branch push) is a hand-off to the human: fail the project as-is — rebase, force-push, and retry stay the human's call.
- Every failure path restores the project to a clean feature branch before moving on (`git merge --abort` + switch back when mid-merge). One project's failure stays inside that project.

## Final report

Per-project table: project, feature branch, commits created, merge result (merged / nothing to merge / failed with reason), target branch pushed or not.
