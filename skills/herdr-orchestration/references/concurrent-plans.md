# Concurrent Plans

One working directory may host several plans at once.

## State and names

State stays apart because each plan has its own directory, and names stay apart because each plan's workers carry its slug prefix.

## Sharing a repo: plan worktree

If this plan shares a repo with another unfinished plan (Setup step 1), exile this plan from the repo's base checkout (or let the user arbitrate the overlap): create a linked worktree `<repo-name>--plan-<slug>` (sibling directory, exactly like task worktrees, SKILL.md: Worktrees) on a plan branch `swarm-plan/<slug>` cut from the base branch. Every edit this plan makes in that repo — base work included — happens there; its task worktrees are created from it (`--cwd`) and merge into the plan branch as usual. The plan branch merges into the base checkout serialized across plans: one plan merges at a time — merge, run verification, report clear before another plan attempts its merge. A merge that conflicts with already-merged work of another plan: rebase the plan branch on the new base, re-run verification, merge again. Never overwrite another plan's merged commits; two unfinished plans never edit one working tree.
