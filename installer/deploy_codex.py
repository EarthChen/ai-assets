"""Phase 2: Codex deploy (plugin symlink, config.toml, AGENTS.md)."""

from __future__ import annotations

import shutil

from . import paths
from .common import create_symlink, ensure_dir, log, log_section


def install_codex(dry_run: bool = False) -> None:
    log_section("Deploying Codex")

    # 1. Plugin symlink
    plugin_dir = paths.CODEX_HOME / "plugins" / "local" / "earthchen-ai-assets"
    create_symlink(paths.REPO_ROOT, plugin_dir, dry_run)

    # Register in config.toml (marketplace + enabled plugin)
    config_path = paths.CODEX_HOME / "config.toml"
    if not dry_run and config_path.exists():
        config_text = config_path.read_text(encoding="utf-8")
        if "earthchen-ai-assets" not in config_text:
            additions = (
                '\n[marketplaces.earthchen-ai-assets]\n'
                'last_updated = "2026-07-10T04:21:00Z"\n'
                'source_type = "local"\n'
                f'source = "{paths.REPO_ROOT}"\n'
                '\n[plugins."earthchen-ai-assets@earthchen-ai-assets"]\n'
                'enabled = true\n'
            )
            config_path.write_text(config_text + additions, encoding="utf-8")
            log("Registered plugin in config.toml")

    log("Plugin provides: skills, MCP")

    # 2. AGENTS.md (plugin can't handle, pre-built in _dist/)
    dist_agents = paths.DIST / "codex" / "AGENTS.md"
    dst_agents = paths.CODEX_HOME / "AGENTS.md"
    if dist_agents.exists():
        if dry_run:
            log(f"[DRY-RUN] write {dst_agents}")
        else:
            ensure_dir(paths.CODEX_HOME)
            shutil.copy2(dist_agents, dst_agents)
            log(f"_dist/codex/AGENTS.md -> {dst_agents}")
