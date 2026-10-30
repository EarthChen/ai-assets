# GitLab MR — one or several projects

Use when the remote is GitLab, or one task spans several projects (a workspace of sibling repos), each needing its own MR. `glab` is the client.

Per project, in order:

1. State: `git -C P status -sb` and `git -C P branch --show-current`. A dirty tree, the default branch, or a detached HEAD stops that project; report it and go on with the others.
2. Bring the default branch in: `git -C P fetch origin`, then `git -C P merge origin/<default>`. A conflict: resolve it with the mechanics in [../../ship-to-test/references/conflict-resolution.md](../../ship-to-test/references/conflict-resolution.md), then run the project's tests before you continue.
3. Push: `git -C P push -u origin <branch>`.
4. Create the MR from inside P (glab reads the cwd):

   ```bash
   cd P && glab mr create --source-branch <branch> --target-branch <default> \
     --title "<conventional title>" --description-file body.md --remove-source-branch --yes
   ```

   Write `body.md` with the `pr` skill. One MR per project; the bodies may reference each other's URLs.
5. Check mergeability: `glab mr view <id> -F json --jq '.detailed_merge_status'`. `mergeable` is the goal; `conflict`, `ci_must_pass`, or `not_approved` go in the report with the MR URL.

Merge only when the user asked for it: `glab mr merge <id> --yes`, adding `--squash` or `--rebase` to match the project's history (Land a Branch, step 5). Projects with a build dependency between them merge in dependency order.

Done when every project has an MR URL and a merge status, or a stated reason it has none.
