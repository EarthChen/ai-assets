---
name: oss-pr-verify
description: "Use when given an upstream PR or issue URL to verify: reproduce in a worktree, judge whether it is a real bug and whether the fix is needed, then draft the review."
---

# Verify an upstream PR or issue

A PR or issue claims a bug and a fix. Reproduce both claims before you judge them. Read access to the repo is enough; write access is not assumed.

## Steps

1. Read the claim: `gh pr view <n> --comments`, `gh pr diff <n>`; for an issue, `gh issue view <n> --comments`. Write down the claimed symptom and the claimed cause in one line each.
2. Isolate: one worktree per PR, following Worktrees in the `git-workflow` skill. Fetch the PR head with `gh pr checkout <n>` inside the worktree.
3. Reproduce before and after. Find the test command in the repo (build files, CI workflow), never assume one. Run the PR's tests, or the smallest test that shows the symptom, on the base commit (expect red), then on the PR head (expect green). A PR with no test: write the smallest reproduction yourself and keep it out of the PR branch.
4. Judge three questions, each with the evidence that decides it:
   - Is it a real bug? (the symptom reproduces on the base commit)
   - Must it be fixed? (who hits it, what breaks, whether a workaround exists)
   - Does the fix change behavior beyond the bug? (callers, defaults, public API, other tests)
5. Draft the review and show it to the user. Pick the verdict by the answers:

   | Answers | Verdict |
   |---|---|
   | real, fix correct, no side effect | approve |
   | real, fix wrong or too wide | request changes, with the failing case and a proposed change |
   | not reproducible, or intended behavior | comment, with what you ran |

6. Submit only after the user confirms the exact text and verdict: `gh pr review <n> --approve|--request-changes|--comment -b "<body>"`. Pushing a fix to the author's branch needs a separate yes.
7. Clean up the worktree and its branch.

Done when the reply holds the three answers, the commands that gave the red and green runs with their key output, the verdict, and the review text.

## Several PRs

Dispatch one subagent per PR, each in its own worktree. Brief each with the PR URL, steps 1 to 4, and "report only; draft the review but do not submit". Collect the reports in one table (PR, three answers, verdict), show it, then submit reviews one by one after the user confirms.
