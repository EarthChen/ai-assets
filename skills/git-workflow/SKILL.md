---
name: git-workflow
description: "Use when committing code, opening a PR or GitLab MR, landing (merging and cleaning up) a branch, branching, or using worktrees: Conventional Commits, GitHub Flow."
---

# Git Workflow

GitHub Flow: every change lands on the default branch through a PR from a feature branch.

## Commit

```
<type>(<scope>)?: <description>

<optional body>
```

Types: feat, fix, refactor, docs, test, chore, perf, ci. Scope is optional. The repository's own convention (`git log`) wins when it differs.

One commit, one concern. Stage the files of the concern by path (`git add <paths>`), so unrelated changes in the tree stay out of the commit.

## Land a Branch

Landing is commit → push → PR → merge → clean up. The user's words set how far to go: "commit" stops at the commit; "commit and push" stops at the push; "commit and merge", "land", "ship to main" run the whole chain. When the words are unclear, stop at the PR and ask.

1. Detect the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`; it may be `main` or `master`). Name it to the user before the first push or merge.
2. Detect the host from `git remote get-url origin`. GitHub: `gh`. GitLab: `glab`, see [references/gitlab-mr.md](references/gitlab-mr.md), which also covers several projects at once and a branch that conflicts with the default branch.
3. First push of a repository: list tracked files over 5 MB and files named `.env*`, `*.pem`, `*.key`, or `id_*`. Each hit needs the user's explicit yes before the push. (A user may commit `.env` to a private repo on purpose; that call is theirs.)
4. Commit on a feature branch cut from the default branch (see Worktrees for where to cut it). Read every commit and `git diff <default>...HEAD`, not the last commit alone. Push with `-u`. Write the PR body with the `pr` skill, plus two parts its template lacks:
   - The first line of **Summary** says in one sentence why the change exists: the problem it solves, or what it makes possible.
   - When the change carries a migration, a compatibility constraint, a deliberate omission or a surprising decision, add `## Special things to note` after Summary, with 1–3 bullets.
5. Merge the way the repository merges: `git log --merges --oneline -5` on the default branch shows merge commits (use `gh pr merge --merge`); linear history means squash or rebase. Wait for the checks (`gh pr checks --watch`) before the merge. `gh pr checks` reporting no checks plus a `CLEAN` merge state means the repository has no CI: merge.
6. Clean up: delete the remote branch, return to the branch the work started from (`git pull --ff-only` when that is the default branch), delete the local branch, then the worktree if one exists.
   - `git branch -d` compares against the current `HEAD`, so it refuses a merged branch while `HEAD` is elsewhere. Check `git merge-base --is-ancestor <branch> origin/<default>`; on success, `git branch -D`.
   - A branch that this session did not create: run `git log <default>..<branch>` first. Unmerged commits mean stop and ask.

Done when `git log origin/<default> -1` shows the merged commit, the branch (local and remote) and any worktree are gone, and the checkout is back on the starting branch with every change of this work committed. Unrelated uncommitted changes stay as they were. Report them, and any step you skipped.

Push the default branch only through a merged PR; force-push never targets it.

## Worktrees

Cut the feature branch in the lightest place that keeps the tree safe:

1. **`git switch -c <branch>`** when `HEAD` is at the default branch's tip, even if the tree holds unrelated uncommitted changes. They ride along; Commit stages only this change's paths. After the merge, `git switch` back to the starting branch: the unrelated changes ride along again.
2. **A worktree** when `switch` would conflict (the default branch moved), when the current branch must stay as it is, or for parallel agents, a hotfix beside work in progress, or a risky experiment.

Worktree mechanics (Herdr or plain git, placement, dependencies, removal): [references/worktrees.md](references/worktrees.md).
