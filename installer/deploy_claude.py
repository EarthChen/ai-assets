"""Phase 2: Claude Code deploy (symlinked skills, agents, CLAUDE.md, rules)."""

from __future__ import annotations

import shutil
import subprocess

from pathlib import Path

from . import paths
from .common import create_symlink, log, log_section
from .deploy_pi import _symlink_target_under
from .shared_skills import link_self_owned_skills
from .third_party import _load_third_party_plugins
from .version import _get_current_version


def _claude_plugins_to_install() -> list[dict]:
    """Filter third-party plugins that are auto-installable on Claude Code.

    A plugin is auto-installable when its claude platform entry has both
    `marketplace_ref` and `plugin_id`. Entries without these (e.g.
    understand-anything's "Managed via ~/.agents/skills/...") are skipped —
    they are managed manually and logged, not auto-installed.

    `marketplace_source` (default "remote") selects the install mode:
      - "local": directory marketplace pointing at REPO_ROOT — no git fetch,
        edits flow immediately after reinstall. `marketplace_ref` is kept
        as the remote-fallback doc path, not used for `marketplace add`.
      - "remote" (default): git clone of `marketplace_ref` (GitHub repo or
        URL); version-gated `plugin update` on refresh.
    """
    result = []
    for plugin in _load_third_party_plugins():
        claude_cfg = plugin.get("platforms", {}).get("claude", {})
        ref = claude_cfg.get("marketplace_ref")
        pid = claude_cfg.get("plugin_id")
        if ref and pid:
            result.append({
                "name": plugin.get("name", pid),
                "marketplace_ref": ref,
                "marketplace_source": claude_cfg.get("marketplace_source", "remote"),
                "plugin_id": pid,
            })
    return result


def _claude_plugin_install(plugin_id: str, ok_suffix: str, fail_verb: str) -> bool:
    """Run `claude plugin install` and log the outcome; True on success."""
    result = subprocess.run(
        ["claude", "plugin", "install", plugin_id, "--scope", "user"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        log(f"{plugin_id} {ok_suffix}")
        return True
    log(f"{plugin_id} {fail_verb} failed: {result.stderr.strip()}")
    return False


def _ensure_claude_plugin(
    installed: str, marketplace_ref: str, marketplace_source: str, plugin_id: str
) -> None:
    """Install or refresh a Claude Code plugin from its marketplace.

    `marketplace_source` picks the path passed to `marketplace add`:
      - "local": REPO_ROOT directory — no git fetch; default for this repo.
      - "remote": the `marketplace_ref` string (git URL).

    Refresh strategy when the plugin is already installed:
      - local: `uninstall` + `install` (reinstall). `plugin update` compares
        the `plugin.json` version field and skips on a match, so it does NOT
        pick up working-tree edits made without a version bump. Reinstall
        forces a fresh snapshot. Idempotent — safe to run every install.
      - remote: `plugin update` (pulls the marketplace ref, version-gated).

    Both paths check the subprocess return code — a silent `update` that logs
    "updated" on failure is the failure mode this guards against. The
    `marketplace add` return code is intentionally not checked: install is the
    real gate (a failed add surfaces as a failed install right after).
    """
    add_source = str(paths.REPO_ROOT) if marketplace_source == "local" else marketplace_ref
    if plugin_id not in installed:
        subprocess.run(
            ["claude", "plugin", "marketplace", "add", add_source],
            capture_output=True, text=True,
        )
        if not _claude_plugin_install(plugin_id, "installed", "install"):
            log(f"Try manually: claude plugin marketplace add {add_source}")
            log(f"             claude plugin install {plugin_id}")
    elif marketplace_source == "local":
        # Local marketplace: plugin update skips on same version, so reinstall
        # to force a fresh snapshot of the working tree.
        subprocess.run(
            ["claude", "plugin", "uninstall", plugin_id],
            capture_output=True, text=True,
        )
        _claude_plugin_install(plugin_id, "reinstalled (local marketplace refresh)", "reinstall")
    else:
        result = subprocess.run(
            ["claude", "plugin", "update", plugin_id],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            log(f"{plugin_id} updated")
        else:
            log(f"{plugin_id} update failed: {result.stderr.strip()}")


def _prune_claude_plugin_cache(plugin_id: str, keep_version: str, dry_run: bool = False) -> None:
    """Delete stale version snapshots of one plugin from Claude's cache.

    Claude keeps every installed version under
    ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/ and its own sweep
    does not reliably remove old ones (a leftover .in_use lock pinned a
    2026-07 snapshot for months). The local marketplace source is the repo
    root, so each snapshot of this repo carries vendor/ submodules too (26M
    measured 2026-10-14). Deletes nothing when the keep-version snapshot is
    missing — a failed reinstall must not wipe the only copy.
    """
    name, _, marketplace = plugin_id.partition("@")
    cache_root = paths.CLAUDE_HOME / "plugins" / "cache" / (marketplace or name) / name
    if not cache_root.is_dir():
        return
    if not (cache_root / keep_version).is_dir():
        log(f"cache prune skipped: {cache_root / keep_version} does not exist")
        return
    removed = 0
    for entry in sorted(cache_root.iterdir()):
        if not entry.is_dir() or entry.name == keep_version:
            continue
        if dry_run:
            log(f"[DRY-RUN] rmtree {entry}")
            removed += 1
            continue
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        shutil.rmtree(entry)
        log(f"removed stale Claude plugin cache {name}/{entry.name}")
        removed += 1
    if removed and not dry_run:
        log(f"{name}: kept {keep_version}, removed {removed} stale snapshot(s)")


def _install_claude_plugins(dry_run: bool) -> None:
    """Install/refresh third-party.json Claude plugins, then prune our cache.

    Installs those declared in third-party.json (claude platform entries with
    marketplace_ref + plugin_id). `marketplace_source` picks the add path:
    "local" (default) = directory at REPO_ROOT, no git fetch; "remote" = git
    clone of marketplace_ref. Requires the `claude` CLI on PATH.
    """
    plugins = _claude_plugins_to_install()
    if dry_run:
        for p in plugins:
            mode = p["marketplace_source"]
            src = str(paths.REPO_ROOT) if mode == "local" else p["marketplace_ref"]
            log(f"[DRY-RUN] claude plugin marketplace add {src} ({mode})")
            log(f"[DRY-RUN] claude plugin install {p['plugin_id']}")
    else:
        # One list call covers all plugins in the config
        list_result = subprocess.run(
            ["claude", "plugin", "list"],
            capture_output=True, text=True,
        )
        installed = list_result.stdout
        for p in plugins:
            _ensure_claude_plugin(
                installed, p["marketplace_ref"], p["marketplace_source"], p["plugin_id"]
            )

    # Local-marketplace plugins are reinstalled from the working tree on every
    # run, so each run leaves another full snapshot behind. Prune our own;
    # remote plugins' caches stay Claude's business.
    for p in plugins:
        if p["marketplace_source"] == "local":
            _prune_claude_plugin_cache(
                p["plugin_id"], _get_current_version(), dry_run
            )


# The repo used to ship to Claude as a plugin. Its skills and agents now load
# from user-level links, so a leftover plugin would load each of them twice.
_LEGACY_PLUGIN_ID = "earthchen-ai-assets@earthchen-ai-assets"
_LEGACY_MARKETPLACE = "earthchen-ai-assets"


def _retire_legacy_plugin(dry_run: bool) -> None:
    """Uninstall the old self plugin and its local marketplace when present."""
    listed = subprocess.run(
        ["claude", "plugin", "list"], capture_output=True, text=True
    ).stdout
    if _LEGACY_PLUGIN_ID not in listed:
        return
    steps = [
        ["claude", "plugin", "uninstall", _LEGACY_PLUGIN_ID],
        ["claude", "plugin", "marketplace", "remove", _LEGACY_MARKETPLACE],
    ]
    for cmd in steps:
        if dry_run:
            log(f"[DRY-RUN] {' '.join(cmd)}")
            continue
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log(f"legacy plugin: {' '.join(cmd[2:])} ok")
        else:
            log(f"legacy plugin: {' '.join(cmd[2:])} failed: {result.stderr.strip()}")


def _link_file(src: Path, dst: Path, dry_run: bool, *, backup: bool = False) -> None:
    """Symlink dst -> src without destroying a real file already at dst.

    A real file identical to src is an old install copy and gets replaced. A
    different one is user data: kept as `<name>.pre-link.bak` when `backup`,
    else the link is skipped with a warning.
    """
    if dst.exists() and not dst.is_symlink():
        if dst.read_bytes() == src.read_bytes():
            if not dry_run:
                dst.unlink()
        elif backup:
            bak = dst.with_name(dst.name + ".pre-link.bak")
            log(f"{'[DRY-RUN] ' if dry_run else ''}kept hand-edited {dst.name} as {bak.name}")
            if not dry_run:
                dst.rename(bak)
        else:
            log(f"WARNING: {dst} is a real file; skipped link to {src}")
            return
    create_symlink(src, dst, dry_run)


def _link_agents(dry_run: bool) -> None:
    """Symlink every agents/<name>.md into ~/.claude/agents/ (user-level agents)."""
    source = paths.REPO_ROOT / "agents"
    if not source.is_dir():
        return
    link_dir = paths.CLAUDE_HOME / "agents"
    source_real = source.resolve()
    if link_dir.is_dir():
        for entry in sorted(link_dir.iterdir()):
            target = _symlink_target_under(entry, source_real)
            if target is not None and not target.exists():
                log(f"{'[DRY-RUN] ' if dry_run else ''}rm stale agent symlink {entry.name}")
                if not dry_run:
                    entry.unlink()
    agents = sorted(source.glob("*.md"))
    for agent in agents:
        _link_file(agent, link_dir / agent.name, dry_run)
    log(f"{len(agents)} agents -> {link_dir}")


def _link_instructions(dry_run: bool) -> None:
    """Link CLAUDE.md and the common rules dir to the generated `_dist/claude` files."""
    dist = paths.DIST / "claude"
    if (dist / "CLAUDE.md").exists():
        _link_file(dist / "CLAUDE.md", paths.CLAUDE_HOME / "CLAUDE.md", dry_run, backup=True)
    rules_src = dist / "rules" / "common"
    rules_dst = paths.CLAUDE_HOME / "rules" / "common"
    if rules_src.exists():
        if rules_dst.is_dir() and not rules_dst.is_symlink():
            # An earlier install copied the rules here; this dir is installer-owned.
            log(f"{'[DRY-RUN] ' if dry_run else ''}replace copied rules dir {rules_dst}")
            if dry_run:
                return
            shutil.rmtree(rules_dst)
        create_symlink(rules_src, rules_dst, dry_run)
        log("Language conventions load on demand via skills/<lang>-development")


def install_claude(dry_run: bool = False) -> None:
    log_section("Deploying Claude Code")

    # 1. Plugins. detect_platforms() also accepts ~/.claude without the CLI,
    # so the plugin steps need their own CLI check; the links do not.
    if shutil.which("claude") is None:
        log("claude CLI not on PATH: skipped plugin install and legacy plugin retirement "
            "(skills, agents, CLAUDE.md and rules still link)")
    else:
        _retire_legacy_plugin(dry_run)
        _install_claude_plugins(dry_run)

    # 2. Links. Skills and agents hot-reload; CLAUDE.md and rules load at
    # session start. MCP has no link: user-scope servers live in ~/.claude.json.
    link_self_owned_skills(dry_run, link_dir=paths.CLAUDE_HOME / "skills")
    _link_agents(dry_run)
    _link_instructions(dry_run)
