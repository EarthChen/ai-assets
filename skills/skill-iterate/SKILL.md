---
name: skill-iterate
description: "Improve a skill after it misfired in real use: find the miss, rewrite, verify with a blind subagent task, land, sync the pin."
disable-model-invocation: true
argument-hint: "[skill]  the skill that misfired (default: the one used in this session)"
---

# Iterate on a skill

A skill misfired: wrong tool, repeated exploration, or a correction from the user. Fix the skill, then prove the fix works on the task that failed.

## Steps

1. Find the miss. Read the session (current, or the one the user names) for the user's corrections, the wrong first command, and exploration that a stable fact would have saved. Ask the user to run `/retro` when the miss spans more than the skill. Write each miss as: task in the user's words → what the agent did → what it should have done.
2. Rewrite the narrowest layer. Call the Skill tool with `writing-for-agents`. A routing miss changes a Route row or the description; a missing stable fact goes into the reference file of its tool; a missing order of work becomes a short reference with a "Done when" line. Derived data (field lists, current values) stays out.
3. Verify with a blind task. Dispatch one subagent per miss:
   - Give it the path to the skill's `SKILL.md` (a user-invoked skill cannot load through the Skill tool, so it reads the path) and the task in the user's words.
   - Leave out the commands, flags, and file names. The skill alone must lead to them.
   - Set the limits: read-only; no file edits, commits, or write operations; a write path stops at the skill's own preview step (for example `--dry-run`).
   - Ask for the references it read, each command it ran, and the answer.

   Pass when the subagent picked the right tool and flags from the skill alone and the answer meets the task's criterion. On a miss, fix the skill, not the prompt, and rerun. Test the skill's CLI or code separately with its own test suite: a unit test does not show that the skill routes to it.
4. Land the change with Land a Branch in the `git-workflow` skill.
5. Sync the pin. A skill vendored into `ai-assets` as `vendor/<name>`:
   - On the dev machine the links point at the dev checkout, so edits are live there already.
   - Other machines read the pin: after the upstream merge, update the submodule to the merged commit (`git -C vendor/<name> pull --ff-only`), commit the pointer in `ai-assets` through its own PR.
   - A new or renamed skill needs `uv run install.py install`, which writes under `~`: ask the user first.

Done when each miss has a passing blind run, the upstream change is merged, and the pin is bumped or the report says why not.
