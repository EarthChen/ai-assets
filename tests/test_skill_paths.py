"""Skill files must not reach outside the skill dir with `${CLAUDE_SKILL_DIR}/..`.

Claude loads a self-owned skill through a symlink (~/.claude/skills/<name> ->
<repo>/skills/<name>). Node, and so Claude Code's Read tool and any `node`
command, normalizes `..` as text before it touches the filesystem, so
`${CLAUDE_SKILL_DIR}/../../vendor/x` becomes `~/.claude/vendor/x` and fails.
`test -f` and `ls` resolve the symlink first and succeed, which hides the bug.
Resolve the real dir with `cd -P` in a script instead, as
skills/show-me/scripts/am does.
"""

from __future__ import annotations

import re
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
_PARENT_REF = re.compile(r"\$\{?CLAUDE_SKILL_DIR\}?/\.\.")


def _parent_refs(skills_root: Path) -> list[str]:
    """`<path>:<line>` for each line that writes `${CLAUDE_SKILL_DIR}/..`."""
    hits = []
    for path in sorted(p for p in skills_root.rglob("*") if p.is_file()):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            if _PARENT_REF.search(line):
                hits.append(f"{path.relative_to(skills_root)}:{number}")
    return hits


def test_parent_ref_through_skill_dir_is_found(tmp_path):
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text('run `node "${CLAUDE_SKILL_DIR}/../../vendor/x.mjs"`\n', encoding="utf-8")
    (skill / "scripts").mkdir()
    (skill / "scripts" / "run").write_text('exec node "$CLAUDE_SKILL_DIR/../lib.mjs"\n', encoding="utf-8")
    (skill / "ok.md").write_text('run "${CLAUDE_SKILL_DIR}/scripts/am"\n', encoding="utf-8")
    assert _parent_refs(tmp_path) == ["demo/SKILL.md:1", "demo/scripts/run:1"]


def test_no_skill_reaches_outside_its_dir_through_the_skill_symlink():
    assert _parent_refs(REAL_REPO / "skills") == [], (
        "Node and Claude Code's Read tool normalize `..` as text, so a symlinked "
        "skill dir plus `..` points outside the repo; resolve with `cd -P` "
        "(see skills/show-me/scripts/am)."
    )
