"""Phase 2: Claude Code deploy (plugins, CLAUDE.md, common rules)."""

from __future__ import annotations

import shutil
import subprocess

from . import paths
from .common import ensure_dir, log, log_section
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


def install_claude(dry_run: bool = False) -> None:
    log_section("Deploying Claude Code")

    # 1. Plugins. detect_platforms() also accepts ~/.claude without the CLI,
    # so the plugin steps need their own CLI check; CLAUDE.md and rules do not.
    if shutil.which("claude") is None:
        log("claude CLI not on PATH: skipped plugin install and cache prune "
            "(CLAUDE.md and rules still deploy)")
    else:
        _install_claude_plugins(dry_run)

    # 2. CLAUDE.md (plugin can't handle)
    dist_claude_md = paths.DIST / "claude" / "CLAUDE.md"
    dst_claude_md = paths.CLAUDE_HOME / "CLAUDE.md"
    if dist_claude_md.exists():
        if dry_run:
            log(f"[DRY-RUN] write {dst_claude_md}")
        else:
            ensure_dir(paths.CLAUDE_HOME)
            shutil.copy2(dist_claude_md, dst_claude_md)
            log(f"_dist/claude/CLAUDE.md -> {dst_claude_md}")

    # 3. Rules: only deploy common/ rules to user-level ~/.claude/rules/
    rules_common_src = paths.DIST / "claude" / "rules" / "common"
    dst_rules = paths.CLAUDE_HOME / "rules" / "common"
    if rules_common_src.exists():
        if dst_rules.exists() and not dry_run:
            # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
            shutil.rmtree(dst_rules)
        ensure_dir(dst_rules, dry_run)
        for rule_file in sorted(rules_common_src.rglob("*.md")):
            rel = rule_file.relative_to(rules_common_src)
            dst = dst_rules / rel
            ensure_dir(dst.parent, dry_run)
            if dry_run:
                log(f"[DRY-RUN] write {dst}")
            else:
                shutil.copy2(rule_file, dst)
        if not dry_run:
            count = sum(1 for _ in rules_common_src.rglob("*.md"))
            log(f"Deployed {count} common rules to {dst_rules}")
            log("Language conventions load on demand via skills/<lang>-development")
