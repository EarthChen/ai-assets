---
name: git-workflow
description: "Use when committing code, opening a PR, branching, or using worktrees: Conventional Commits, GitHub Flow."
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

## Worktrees

Use `git worktree` instead of stash + branch-switching when work must proceed in parallel:

- Parallel independent tasks on the same repo (especially multiple agents working simultaneously — one worktree per agent avoids write conflicts)
- Hotfix while a feature branch has work in progress
- Risky experiments that should not touch the main working tree

Before creating a worktree, check `HERDR_ENV`. `HERDR_ENV=1` means the session runs inside Herdr: use the `herdr` skill and `herdr worktree` for the whole lifecycle. A hook denies `git worktree add` and `EnterWorktree` creation there. Otherwise use `git worktree add`.

Herdr lifecycle:

- Create: `herdr worktree create --branch <name> --base <ref>`. Herdr picks the path (`~/.herdr/worktrees/<repo>/<branch>`) and opens a workspace.
- Enter: `EnterWorktree` with `path` switches the session into it.
- Remove after merge: `herdr worktree remove --workspace <id>`, then `git branch -d <branch>`. Herdr deletes the checkout only, so the branch stays.

Conventions (the placement rule applies to plain git only; Herdr owns its path):

- Place worktrees OUTSIDE the repo directory (e.g. sibling `../<repo>-<branch>`), never inside it — nested worktrees pollute file search and tooling scans
- One branch = one worktree; a branch cannot be checked out in two worktrees
- Dependencies and env files (`node_modules/`, `.venv/`, `.env`) are NOT shared — reinstall/copy per worktree before running anything
- Clean up after merge: `git worktree remove <path>`, then `git worktree prune`; do not leave stale worktrees behind
