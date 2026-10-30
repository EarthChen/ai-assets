---
name: git-workflow
description: "Use when committing code, opening a PR or GitLab MR, landing (merging and cleaning up) a branch, branching, or using worktrees: Conventional Commits, GitHub Flow."
---

# Git Workflow — Branching, Commits, PR & Worktrees

## Branching Strategy

Follow GitHub Flow, generalized to the repo's default branch (may be `main` or `master` — detect it, do not assume):

- The default branch is the stable branch; all feature/fix branches are cut from it and merged back via PR
- Do not commit directly to the default branch
- Never force-push the default branch

## Commit Message Format

```
<type>(<scope>)?: <description>

<optional body>
```

Types: feat, fix, refactor, docs, test, chore, perf, ci

Scope is optional (e.g. `feat(skills): ...`). Follow the repository's existing convention when one exists (check `git log`).

Keep commits atomic: one commit addresses one concern.

## Pull Request Workflow

When creating PRs:

1. Analyze full commit history (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Write the body: call the Skill tool with "pr"
4. Push with `-u` flag if new branch

## Land a Branch

Landing is commit → push → PR → merge → clean up. The user's words set how far to go: "commit" stops at the commit; "commit and push" stops at the push; "commit and merge", "land", "ship to main" run the whole chain. When the words are unclear, stop at the PR and ask.

1. Detect the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`). Name it to the user before the first push or merge.
2. Detect the host from `git remote get-url origin`. GitHub: `gh`. GitLab: `glab`, see [references/gitlab-mr.md](references/gitlab-mr.md), which also covers several projects at once and a branch that conflicts with the default branch.
3. First push of a repository: list tracked files over 5 MB and files named `.env*`, `*.pem`, `*.key`, or `id_*`. Each hit needs the user's explicit yes before the push. (A user may commit `.env` to a private repo on purpose; that call is theirs.)
4. Work on a feature branch, never on the default branch. Write the PR body with the `pr` skill.
5. Merge the way the repository merges: `git log --merges --oneline -5` on the default branch shows merge commits (use `gh pr merge --merge`); linear history means squash or rebase. Wait for the checks (`gh pr checks --watch`) before the merge.
6. Clean up: delete the remote branch, `git switch <default>`, `git pull --ff-only`, `git branch -d <branch>`, then the worktree (Worktrees, below). Before you delete a branch that this session did not create, run `git log <default>..<branch>`: unmerged commits mean stop and ask.

Done when `git log origin/<default> -1` shows the merged commit, the local checkout sits on the default branch with a clean tree, and the branch and worktree are gone. Report any step you skipped.

## Worktrees

Use `git worktree` instead of stash + branch-switching when work must proceed in parallel:

- Parallel independent tasks on the same repo (especially multiple agents working simultaneously — one worktree per agent avoids write conflicts)
- Hotfix while a feature branch has work in progress
- Risky experiments that should not touch the main working tree

Before creating a worktree, check `HERDR_ENV`. `HERDR_ENV=1` means the session runs inside Herdr: use the `herdr` skill and `herdr worktree` for the whole lifecycle. Otherwise use `git worktree add`.

Herdr lifecycle:

- Create: `herdr worktree create --branch <name> --base <ref>`. Herdr picks the path (`~/.herdr/worktrees/<repo>/<branch>`) and opens a workspace.
- Enter: `EnterWorktree` with `path` switches the session into it.
- Remove after merge: `herdr worktree remove --workspace <id>`, then `git branch -d <branch>`. Herdr deletes the checkout only, so the branch stays.

Conventions (the placement rule applies to plain git only; Herdr owns its path):

- Place worktrees OUTSIDE the repo directory (e.g. sibling `../<repo>-<branch>`), never inside it — nested worktrees pollute file search and tooling scans
- One branch = one worktree; a branch cannot be checked out in two worktrees
- Dependencies and env files (`node_modules/`, `.venv/`, `.env`) are NOT shared — reinstall/copy per worktree before running anything
- Clean up after merge: `git worktree remove <path>`, then `git worktree prune`; do not leave stale worktrees behind
