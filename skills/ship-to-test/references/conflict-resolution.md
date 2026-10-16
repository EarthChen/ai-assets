# Conflict resolution

Resolve conflicts yourself by default; hand to the human only the hunks whose intent you cannot distinguish. Gate every conflicting hunk first:

- **Deterministic** — both sides' intent survives mechanically: pure additions with no semantic overlap (keep both), lockfile conflicts (regenerate with the package manager), one side a strict subset of the other (take the superset). Resolve these directly.
- **Ambiguous** — the sides are incompatible and a choice is required: present both sides' intent plus your suggested resolution, then wait for the human's decision. Anything not clearly deterministic is ambiguous.

Mechanics for every hunk you keep:

1. **Read the primary sources** — the commit messages, PRs, and tickets behind each side. Resolve two intents, not two text blocks. Never resolve by flag (`--ours`, `--theirs`) or by deleting the block that looks less important.
2. **Preserve both intents** where they are compatible. Where they are not, keep the side matching the merge's goal and name the dropped intent in the commit message. Invent no new behaviour.
3. **Finish the operation** — stage everything, then commit.
