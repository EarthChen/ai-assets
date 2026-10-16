"""Shared step: self-owned skills in the Agent Skills standard dir."""

from __future__ import annotations

from pathlib import Path

from . import paths
from .common import create_symlink, log
from .deploy_pi import _clean_stale_skill_symlinks


def link_self_owned_skills(dry_run: bool = False, link_dir: Path | None = None) -> None:
    """Symlink every skills/<name> dir into ~/.agents/skills/ (or `link_dir`).

    ~/.agents/skills is the Agent Skills standard dir. pi, Cursor and Codex
    read self-owned skills only from there (the Cursor plugin copy omits
    skills/ and Codex loads no repo plugin), so this runs on every install,
    whatever platforms are deployed. Claude does not read the dir; it passes
    ~/.claude/skills as `link_dir`. Third-party links and real directories in
    the dir are left alone.
    """
    source = paths.REPO_ROOT / "skills"
    if not source.is_dir():
        return
    shared = link_dir or paths.AGENTS_HOME / "skills"
    _clean_stale_skill_symlinks(shared, source, dry_run)
    count = 0
    for skill_dir in sorted(source.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        create_symlink(skill_dir, shared / skill_dir.name, dry_run)
        count += 1
    log(f"{count} self-owned skills -> {shared}")
