"""Phase 2: Codex deploy (AGENTS.md; retires the old repo plugin)."""

from __future__ import annotations

import re
import shutil

from . import paths
from .common import ensure_dir, log, log_section

_PLUGIN_ID = "earthchen-ai-assets@earthchen-ai-assets"
_PLUGIN_ENABLED = re.compile(
    r'(\[plugins\."' + re.escape(_PLUGIN_ID) + r'"\][^\[]*?enabled\s*=\s*)true')


def _retire_repo_plugin(dry_run: bool) -> None:
    """Disable the repo plugin an older install registered.

    The plugin carried only skills plus an empty MCP file, and Codex loads a
    plugin from a cached snapshot, so it served stale skills next to the
    ~/.agents/skills links. Removes the local symlink into this repo and
    flips `enabled` to false; the rest of config.toml and Codex's plugin
    cache stay untouched.
    """
    link = paths.CODEX_HOME / "plugins" / "local" / "earthchen-ai-assets"
    if link.is_symlink() and link.resolve() == paths.REPO_ROOT.resolve():
        if dry_run:
            log(f"[DRY-RUN] rm {link}")
        else:
            link.unlink()
            log(f"Removed retired plugin link {link}")
    config_path = paths.CODEX_HOME / "config.toml"
    if not config_path.exists():
        return
    text = config_path.read_text(encoding="utf-8")
    new_text = _PLUGIN_ENABLED.sub(r"\1false", text)
    if new_text == text:
        return
    if dry_run:
        log(f"[DRY-RUN] disable {_PLUGIN_ID} in {config_path}")
        return
    config_path.write_text(new_text, encoding="utf-8")
    log(f"Disabled retired plugin {_PLUGIN_ID} in {config_path}")


def install_codex(dry_run: bool = False) -> None:
    log_section("Deploying Codex")

    # 1. Skills come from ~/.agents/skills (shared install step); no plugin.
    _retire_repo_plugin(dry_run)

    # 2. AGENTS.md (pre-built in _dist/)
    dist_agents = paths.DIST / "codex" / "AGENTS.md"
    dst_agents = paths.CODEX_HOME / "AGENTS.md"
    if dist_agents.exists():
        if dry_run:
            log(f"[DRY-RUN] write {dst_agents}")
        else:
            ensure_dir(paths.CODEX_HOME)
            shutil.copy2(dist_agents, dst_agents)
            log(f"_dist/codex/AGENTS.md -> {dst_agents}")
