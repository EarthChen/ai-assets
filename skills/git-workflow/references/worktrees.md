# Worktree mechanics

Read when `SKILL.md`, Worktrees, picks a worktree. Prefer a worktree over stash + branch-switching: a stash is easy to lose, and a switch reinstalls dependencies.

Check `HERDR_ENV` first. `HERDR_ENV=1` means the session runs inside Herdr: use the `herdr` skill and `herdr worktree` for the whole lifecycle. Otherwise use `git worktree add`.

## Herdr lifecycle

- Create: `herdr worktree create --branch <name> --base <ref>`. Herdr picks the path (`~/.herdr/worktrees/<repo>/<branch>`) and opens a workspace.
- Enter: `EnterWorktree` with `path` switches the session into it.
- Remove after merge: `herdr worktree remove --workspace <id>`, then delete the branch if it remains (`git branch --list <branch>`; deletion rules: `SKILL.md`, Land a Branch, step 6).

## Plain git

- Place worktrees outside the repo directory, as a sibling `../<repo>-<branch>`: a nested worktree pollutes file search and tooling scans.
- Remove after merge: `git worktree remove <path>`, then `git worktree prune`.

## Both

- One branch, one worktree: a branch checks out in one place only.
- Dependencies and env files (`node_modules/`, `.venv/`, `.env`) stay in the original tree. Reinstall or copy them into the worktree before you run anything.
- Move an uncommitted change into the worktree with a copy of its paths, then `git status` there: the list must match the change. The original tree still shows those paths as modified after the merge: `git restore` them before its branch takes in the default branch.
- Leave no stale worktree behind.
