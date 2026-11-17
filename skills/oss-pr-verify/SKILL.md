---
name: oss-pr-verify
description: "Use when given an upstream PR or issue URL to verify: reproduce in a worktree, judge whether it is a real bug and whether the fix is needed, then draft the review."
---

# Verify an upstream PR or issue

A PR or issue claims a bug and a fix. Reproduce both claims before you judge them. Read access to the repo is enough; write access is not assumed.

## Steps

1. Read the claim: `gh pr view <n> --comments`, `gh pr diff <n>`; for an issue, `gh issue view <n> --comments`. Write down the claimed symptom and the claimed cause in one line each.
2. Isolate: one worktree per PR, following Worktrees in the `git-workflow` skill. Fetch the PR head with `gh pr checkout <n>` inside the worktree.
3. Reproduce before and after. Find the test command in the repo (build files, CI workflow), never assume one. Run the PR's tests, or the smallest test that shows the symptom, on the base commit (expect red), then on the PR head (expect green). In multi-module builds (Maven/Gradle), run from the repo root with upstream modules built (`-am` for Maven) and a permissive no-match flag (`-Dsurefire.failIfNoSpecifiedTests=false`), or filtered `-Dtest` runs fail on modules without the test. A PR with no test: write the smallest reproduction yourself and keep it out of the PR branch.
4. Judge along four lenses, each answer backed by evidence you ran, not by reading the diff:
   - **Correctness** — is it a real bug, fixed rightly? The symptom reproduces on the base commit; name the failure mechanism (the exception or wrong value at the receiving call site), not just a red test. The PR's test must be a real witness: it drives the actual failure path (real codecs, parsers, and wire formats, not mocks of the component under test), and you state the layer it leaves uncovered (unit vs integration vs deployment). Check the fix against the authoritative spec or reference implementation it claims to satisfy — a round-trip through the repo's own decoder proves self-consistency, not spec conformance (watch for spec-pinned details a self-test cannot see, e.g. an encoding alphabet). Search for sibling call sites handling the same field or protocol that the PR left broken.
   - **Necessity** — must it be fixed? Who hits it, and is the broken path default or opt-in config; what breaks; is the workaround real (reachable at a documented extension point); check the tracker for prior maintainer stance, reverted fixes, or a standing disposition for this class of report.
   - **Best fix** — is this the optimal way? Name the rejected alternatives (e.g. pushing the fix to a lower layer so all callers inherit it, or shifting responsibility to callers) and why this one wins on blast radius and idempotency; match the reference implementation's choice where one exists; items the author scopes out are follow-up suggestions, not blockers.
   - **Side effects** — does anything change beyond the bug? Callers, defaults, public API, other tests, and external consumers who may have adapted to the old broken output.
5. Draft the review and show it to the user. Pick the verdict by the answers:

   | Answers | Verdict |
   |---|---|
   | real, fix correct, no side effect | approve |
   | real, fix wrong or too wide | request changes, with the failing case and a proposed change |
   | real, fix correct, but unnecessary (opt-in path, real workaround) | comment, citing the workaround and the impact that argues for or against fixing |
   | not reproducible, or intended behavior | comment, with what you ran |

   Write the review text in the language the upstream repo already uses (check recent PR reviews and issue comments there), not the chat language. Say which language the draft is in when you show it.
   When your report explains a failure mechanism spanning three or more components, load the `show-me` skill and draw that call chain as one inline diagram for the user; keep the upstream review text plain unless the user asks to embed the diagram.

6. Submit only after the user confirms the exact text and verdict: `gh pr review <n> --approve|--request-changes|--comment -b "<body>"`. Pushing a fix to the author's branch needs a separate yes.
7. Clean up the worktree and its branch.

Done when the reply holds the step-4 answers, the commands that gave the red and green runs with their key output, the verdict, and the review text.

## Several PRs

Dispatch one subagent per PR, each in its own worktree. Brief each with the PR URL, steps 1 to 4, and "report only; draft the review but do not submit". Collect the reports in one table (PR, step-4 answers, verdict), show it, then submit reviews one by one after the user confirms.
