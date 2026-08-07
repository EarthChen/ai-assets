---
name: git-workflow
description: Use when creating pull requests (analyze history, draft PR summary, test plan) or working with git worktrees (parallel agents, hotfixes, risky experiments)
metadata:
  origin: ECC
---

# Git Workflow — PR & Worktrees

## When to Use

Use this skill when you need to open a pull request (analyze full commit history, draft the PR summary with a test plan, push a new branch with `-u`) or when parallel work requires a git worktree (multiple agents, hotfixes while a feature branch is in progress, risky experiments that must not touch the main working tree).

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
