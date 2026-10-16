"""Phase 2: Cursor deploy (real-directory plugin copy)."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import paths
from .common import ensure_dir, log, log_section

# Directories that must NOT be copied into a platform's local-plugin
# directory. .git/ is VCS metadata (a real-dir plugin is a snapshot, not a
# working clone); __pycache__/.venv/ and the ruff/pytest caches are Python
# tool artifacts; node_modules/ is the VitePress toolchain; .playwright-mcp/
# is MCP session state; vendor/ holds git submodules already installed
# manually into ~/.agents/skills/ (copying them in would duplicate and they're
# not committed real files anyway); .in_use/ is a PID-marker dir created
# during local iteration. These names are skipped at every depth.
_PLUGIN_COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    "__pycache__",
    ".venv",
    ".playwright-mcp",
    "vendor",
    ".in_use",
    "node_modules",
    ".ruff_cache",
    ".pytest_cache",
)


# Matched only at the repo root, because a skill may legitimately ship a
# subdir with one of these generic names: local working state (.claude/
# settings.local.json and plans, .agents/, notes/) and skills/. Cursor reads
# self-owned skills from ~/.agents/skills; a root skills/ in the plugin
# copy is auto-discovered (no manifest field needed) and loads them twice.
_PLUGIN_COPY_IGNORE_ROOT_ONLY = frozenset({".claude", ".agents", "notes", "skills"})


def _plugin_copy_ignore(src_root: Path):
    """copytree ignore callable: any-depth patterns + root-only names."""
    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = set(_PLUGIN_COPY_IGNORE(directory, names))
        if Path(directory) == src_root:
            ignored |= _PLUGIN_COPY_IGNORE_ROOT_ONLY.intersection(names)
        return ignored
    return ignore


def copy_plugin_tree(src: Path, dst: Path, dry_run: bool = False) -> None:
    """Copy the repo as a real directory (rsync-style), not a symlink.

    Cursor's local-plugin scanner (~/.cursor/plugins/local/) skips
    symlinks — a symlinked plugin dir is never indexed, so its skills
    never load. A real-directory copy is. This replaces the symlink
    that install_cursor previously used; Codex keeps create_symlink
    (its scanner follows symlinks fine).

    Semantics mirror `rsync -a --delete`: the destination is rebuilt
    from scratch each run, so files deleted from the source also
    disappear from the destination. `symlinks=True` preserves repo-root
    symlinks as-is rather than dereferencing them.
    """
    ensure_dir(dst.parent, dry_run)
    if dst.exists() or dst.is_symlink():
        if dry_run:
            log(f"[DRY-RUN] rmtree {dst}")
        else:
            if dst.is_symlink():
                dst.unlink()
            else:
                # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
                shutil.rmtree(dst)
    if dry_run:
        log(f"[DRY-RUN] copy tree {src} -> {dst}")
        return
    shutil.copytree(
        src, dst, symlinks=True, ignore=_plugin_copy_ignore(src), dirs_exist_ok=False
    )
    log(f"Copied plugin tree {dst.name} <- {src}")


def install_cursor(dry_run: bool = False) -> None:
    log_section("Deploying Cursor")

    # 1. Local plugin as a REAL-DIRECTORY copy (rsync-style), not a symlink.
    #    docs: https://cursor.com/docs/plugins#test-plugins-locally —
    #    "load your plugin from ~/.cursor/plugins/local" + Restart Cursor or
    #    Developer: Reload Window. The docs mention a symlink as a "faster
    #    iteration" option, BUT Cursor's local-plugin scanner skips symlinks
    #    in practice (verified on Cursor 2.5.x: a symlinked
    #    ~/.cursor/plugins/local/<name> is never indexed — its skills never
    #    appear, scope stays user:skill only). Only a real-directory copy gets
    #    scanned and loaded as plugin:skill. So we copy the repo tree (excluding
    #    .git/.venv/vendor/etc — see copy_plugin_tree) and rebuild it each run
    #    for rsync --delete semantics: edits in the repo flow through on the
    #    next `install.py install`. Codex keeps create_symlink — its scanner
    #    follows symlinks fine, so there was no reason to match Cursor here.
    local_plugin = paths.CURSOR_HOME / "plugins" / "local" / "earthchen-ai-assets"
    copy_plugin_tree(paths.REPO_ROOT, local_plugin, dry_run)
    if not dry_run:
        log("Local plugin installed → Restart Cursor or Developer: Reload Window")

    # 2. Marketplace alternative. install.py cannot install/uninstall a
    #    marketplace plugin itself — `cursor` CLI has no `plugin` subcommand
    #    (only editor-launch flags), so marketplace install is a UI-only action
    #    (Settings → Customize → add URL). Offered here as the parallel option.
    #    Local + marketplace under the same plugin name would double-load;
    #    pick one. A marketplace install also ships skills/, which duplicates
    #    the ~/.agents/skills links, so the local copy is the supported path.
    log("Plugin provides: rules, agents, MCP (skills come from ~/.agents/skills)")
    log("Marketplace alternative: Settings → Customize → add URL")
    log("  https://github.com/EarthChen/ai-assets")
    log("  (local + marketplace same-name double-loads; use one)")
