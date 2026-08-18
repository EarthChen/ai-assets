---
name: git-workflow
description: "Git conventions: Conventional Commits, GitHub Flow branching, PR process, worktrees. Use when committing code, opening a PR, or using worktrees."
---

# Git Workflow — Branching, Commits, PR & Worktrees

## When to Use

Use this skill when committing code (conventional commit format), opening a pull request (analyze history, draft summary with test plan), or when parallel work requires a git worktree (multiple agents, hotfixes, risky experiments).

## Branching Strategy

Follow GitHub Flow, generalized to the repo's default branch (may be `main` or `master` — detect it, do not assume):

- The default branch is the stable branch; all feature/fix branches are cut from it and merged back via PR
- Do not commit directly to the default branch
- Never force-push the default branch

## Commit Message Format

```
<type>: <description>

<optional body>
```

Types: feat, fix, refactor, docs, test, chore, perf, ci

Keep commits atomic: one commit addresses one concern.

## Pull Request Workflow

When creating PRs:

1. Analyze full commit history (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Draft comprehensive PR summary
4. Include test plan with TODOs
5. Push with `-u` flag if new branch

## Worktrees

Use `git worktree` instead of stash + branch-switching when work must proceed in parallel:

- Parallel independent tasks on the same repo (especially multiple agents working simultaneously — one worktree per agent avoids write conflicts)
- Hotfix while a feature branch has work in progress
- Risky experiments that should not touch the main working tree

Conventions:

- Place worktrees OUTSIDE the repo directory (e.g. sibling `../<repo>-<branch>`), never inside it — nested worktrees pollute file search and tooling scans
- One branch = one worktree; a branch cannot be checked out in two worktrees
- Dependencies and env files (`node_modules/`, `.venv/`, `.env`) are NOT shared — reinstall/copy per worktree before running anything
- Clean up after merge: `git worktree remove <path>`, then `git worktree prune`; do not leave stale worktrees behind
