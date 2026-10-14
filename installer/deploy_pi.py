"""Phase 2: pi deploy (AGENTS.md, skill and agent symlinks)."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import paths
from .common import create_symlink, ensure_dir, log, log_section


def _symlink_target_under(entry: Path, source_real: Path) -> Path | None:
    """Return entry's link target if entry is a symlink resolving under
    source_real (an already-resolved dir); otherwise None."""
    if not entry.is_symlink():
        return None
    target = entry.readlink()
    if not target.is_absolute():
        target = entry.parent / target
    try:
        target.resolve().relative_to(source_real)
    except ValueError:
        return None
    return target


def _remove_self_owned_skill_links(link_dir: Path, dry_run: bool = False) -> None:
    """Remove symlinks in link_dir that resolve into this repo's skills/.

    Self-owned skills link into ~/.agents/skills. A link to one of them in
    ~/.pi/agent/skills (left by an older install) makes pi load it twice.
    Links into pi/skills/, third-party links and real directories stay.
    """
    if not link_dir.is_dir():
        return
    source_real = (paths.REPO_ROOT / "skills").resolve()
    count = 0
    for entry in sorted(link_dir.iterdir()):
        if _symlink_target_under(entry, source_real) is None:
            continue
        if dry_run:
            log(f"[DRY-RUN] rm self-owned skill symlink {entry}")
            count += 1
            continue
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        entry.unlink()
        count += 1
    if count and not dry_run:
        log(f"{link_dir}: self-owned skill symlinks removed ({count})")


def _clean_stale_skill_symlinks(link_dir: Path, source_root: Path, dry_run: bool = False) -> None:
    """Remove stale skill symlinks in link_dir that point into source_root.

    All local skills install from this repo: install_pi symlinks every
    skills/<name> dir into ~/.agents/skills/ and every pi/skills/<name> dir
    into ~/.pi/agent/skills/. Each call cleans only links into its own
    source_root. When a skill dir is renamed or
    removed in the repo, its link outlives it — every platform scanning the
    dir then loads a ghost or trips on a broken link. Any symlink whose
    target resolves under source_root and no longer holds a SKILL.md is
    stale and removed. Third-party links (pointing into vendor/) are not
    touched — their lifecycle belongs to install_manual_skills.
    """
    if not link_dir.is_dir():
        return
    source_real = source_root.resolve()
    count = 0
    for entry in sorted(link_dir.iterdir()):
        target = _symlink_target_under(entry, source_real)
        if target is None:
            continue  # not a link, or owned elsewhere (vendor/, other repos)
        if target.exists() and (target / "SKILL.md").exists():
            continue
        if dry_run:
            log(f"[DRY-RUN] rm stale skill symlink {entry.name}")
            count += 1
            continue
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        entry.unlink()
        count += 1
    if count and not dry_run:
        log(f"{link_dir}: stale skill symlinks removed ({count})")


def _clean_stale_agent_symlinks(link_dir: Path, source_root: Path, dry_run: bool = False) -> None:
    """Remove stale agent symlinks in link_dir that point into source_root.

    Symmetric to _clean_stale_skill_symlinks but for *.md agent files:
    install symlinks every agents/*.md into ~/.pi/agent/agents/. When an
    agent file is renamed or removed in the repo, its link outlives it —
    pi-subagents' discoverAgents() scans that dir and loads *.md, so a broken
    link to a deleted agent is a ghost the harness must skip or fail on.
    Any symlink whose target resolves under source_root and no longer exists
    is stale and removed. Third-party links (pointing into vendor/) are not
    touched.
    """
    if not link_dir.is_dir():
        return
    source_real = source_root.resolve()
    count = 0
    for entry in sorted(link_dir.iterdir()):
        target = _symlink_target_under(entry, source_real)
        if target is None:
            continue  # not a link, or owned elsewhere (vendor/, other repos)
        if target.exists() and target.is_file():
            continue
        if dry_run:
            log(f"[DRY-RUN] rm stale agent symlink {entry.name}")
            count += 1
            continue
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        entry.unlink()
        count += 1
    if count and not dry_run:
        log(f"{link_dir}: stale agent symlinks removed ({count})")


def install_pi(dry_run: bool = False) -> None:
    """Deploy to the pi coding agent (badlogic/pi-mono).

    pi has no plugin system compatible with this repo, so the script deploys
    directly:
    - AGENTS.md (global instructions + common rules) -> ~/.pi/agent/AGENTS.md
      (full overwrite, same as the Codex deploy)
    - self-owned skills (skills/*) symlinked into ~/.agents/skills/ — the
      Agent Skills standard dir that pi and other compliant harnesses scan,
      next to the third-party manual installs (mattpocock, anysearch, ...).
      Codex and Cursor also scan it and get the same skills from their
      plugin, so they may list each skill twice (accepted trade-off)
    - pi-only skills (pi/skills/*) symlinked into ~/.pi/agent/skills/ — read
      by pi only, outside the plugin-root skills/, so they never reach
      Claude/Codex/Cursor
    - pi-only agents (pi/agents/*.md) symlinked into ~/.pi/agent/agents/
      alongside agents/*.md (step 3b) — outside the plugin-root agents/ that
      Claude auto-scans and Cursor's manifest declares, so these load
      exclusively on pi
    - agents/*.md symlinked into ~/.pi/agent/agents/ — pi-subagents'
      discoverAgents() scans that user dir (userDirOld = getAgentDir()/agents)
      and loads *.md with YAML frontmatter. Repo agent frontmatter only
      sets name + description; model and tools are intentionally omitted so
      pi-subagents inherits the parent session's model and grants the default
      tool set — verify loading with /subagents-doctor +
      subagent({ action: "list" }) after install.

    NOT deployed: MCP (pi covers playwright etc. via its own extensions),
    separate rules files (embedded in AGENTS.md; language conventions load
    on demand via skills/<lang>-development).
    """
    log_section("Deploying pi")

    # 1. AGENTS.md (full overwrite — repo is the single source of truth)
    dist_agents = paths.DIST / "pi" / "AGENTS.md"
    dst_agents = paths.PI_AGENT_HOME / "AGENTS.md"
    if dist_agents.exists():
        if dry_run:
            log(f"[DRY-RUN] write {dst_agents}")
        else:
            ensure_dir(paths.PI_AGENT_HOME)
            shutil.copy2(dist_agents, dst_agents)
            log(f"_dist/pi/AGENTS.md -> {dst_agents}")

    # 2. Skills: symlink self-owned skills into ~/.agents/skills/, the
    # Agent Skills standard dir pi scans natively.
    shared_skills = paths.AGENTS_HOME / "skills"
    _clean_stale_skill_symlinks(shared_skills, paths.REPO_ROOT / "skills", dry_run)
    count = 0
    for skill_dir in sorted((paths.REPO_ROOT / "skills").iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        create_symlink(skill_dir, shared_skills / skill_dir.name, dry_run)
        count += 1
    log(f"{count} self-owned skills -> {shared_skills}")

    # 2b. pi-only skills: symlink pi/skills/*/ into ~/.pi/agent/skills/,
    # which only pi reads. Self-owned links there (older installs) would
    # make pi load those skills twice, so they go.
    pi_skills_dst = paths.PI_AGENT_HOME / "skills"
    _remove_self_owned_skill_links(pi_skills_dst, dry_run)
    pi_skills_src = paths.REPO_ROOT / "pi" / "skills"
    _clean_stale_skill_symlinks(pi_skills_dst, pi_skills_src, dry_run)
    count = 0
    for skill_dir in sorted(pi_skills_src.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        create_symlink(skill_dir, pi_skills_dst / skill_dir.name, dry_run)
        count += 1
    log(f"{count} pi-only skills -> {pi_skills_dst}")

    # 3. Agents: symlink repo agents/*.md into the pi-subagents user dir
    # (~/.pi/agent/agents/). pi-subagents' discoverAgents() scans this dir
    # (userDirOld = getAgentDir()/agents) and loads *.md with YAML frontmatter
    # alongside its builtins (scout/reviewer/worker/...). Repo agent
    # frontmatter only sets name + description; model/tools are omitted so
    # pi-subagents inherits the parent session's model and grants the
    # default tool set. Verify with /subagents-doctor +
    # subagent({ action: "list" }) after install.
    pi_agents_dir = paths.PI_AGENT_HOME / "agents"
    agents_src = paths.REPO_ROOT / "agents"
    _clean_stale_agent_symlinks(pi_agents_dir, agents_src, dry_run)
    count = 0
    for agent_file in sorted(agents_src.glob("*.md")):
        create_symlink(agent_file, pi_agents_dir / agent_file.name, dry_run)
        count += 1
    log(f"{count} agents -> {pi_agents_dir}")
    # 3b. pi-only agents: symlink pi/agents/*.md into the same dir. They live
    # outside the plugin-root agents/ dir Claude auto-scans and outside the
    # ./agents/ path Cursor's manifest declares, so these load exclusively on
    # pi and never on Claude/Codex/Cursor.
    agents_pi_src = paths.REPO_ROOT / "pi" / "agents"
    _clean_stale_agent_symlinks(pi_agents_dir, agents_pi_src, dry_run)
    count = 0
    for agent_file in sorted(agents_pi_src.glob("*.md")):
        create_symlink(agent_file, pi_agents_dir / agent_file.name, dry_run)
        count += 1
    log(f"{count} pi-only agents -> {pi_agents_dir}")

    log("Note: MCP not deployed (pi provides playwright etc. via its own extensions)")
