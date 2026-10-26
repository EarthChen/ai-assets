"""Plugin version management across the platform manifests."""

from __future__ import annotations

import json

from . import paths
from .common import log, log_section


def _get_current_version() -> str:
    """Highest version across the platform manifests.

    Reading the first available file instead let drift silently re-issue an
    existing version: with .cursor-plugin at 1.3.0 and .claude-plugin at 1.3.1,
    `version --bump patch` computed 1.3.0 -> 1.3.1 and wrote 1.3.1 everywhere
    (hit 2026-10-08). set_version keeps them aligned, so the max is the
    base a bump should start from.
    """
    def sort_key(ver: str) -> tuple:
        parts = [int(p) for p in ver.split(".")[:3] if p.isdigit()]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)

    versions = []
    for pj in paths.PLUGIN_JSONS:
        if not pj.exists():
            continue
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        data = json.loads(pj.read_text(encoding="utf-8"))
        ver = data.get("version")
        if ver:
            versions.append(ver)
    if not versions:
        return "0.0.0"
    return max(versions, key=sort_key)


def _bump_version(current: str, part: str) -> str:
    """Bump major/minor/patch of a semver string."""
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    parts = [int(x) for x in current.split(".")]
    while len(parts) < 3:
        parts.append(0)
    if part == "major":
        parts = [parts[0] + 1, 0, 0]
    elif part == "minor":
        parts = [parts[0], parts[1] + 1, 0]
    elif part == "patch":
        parts = [parts[0], parts[1], parts[2] + 1]
    return ".".join(str(x) for x in parts)


def set_version(version: str, dry_run: bool = False) -> None:
    """Set version across all plugin.json files and marketplace.json."""
    log_section(f"Setting version to {version}")
    for pj in paths.PLUGIN_JSONS:
        if not pj.exists():
            continue
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        data = json.loads(pj.read_text(encoding="utf-8"))
        old_ver = data.get("version", "unknown")
        data["version"] = version
        if dry_run:
            log(f"[DRY-RUN] {pj.relative_to(paths.REPO_ROOT)}: {old_ver} -> {version}")
        else:
            pj.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            log(f"{pj.relative_to(paths.REPO_ROOT)}: {old_ver} -> {version}")

    # Update marketplace.json version (critical for Claude Code auto-update)
    if paths.MARKETPLACE_JSON.exists():
        # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
        data = json.loads(paths.MARKETPLACE_JSON.read_text(encoding="utf-8"))
        for plugin in data.get("plugins", []):
            if plugin.get("name") == "earthchen-ai-assets":
                old_ver = plugin.get("version", "unknown")
                plugin["version"] = version
                if dry_run:
                    log(f"[DRY-RUN] {paths.MARKETPLACE_JSON.relative_to(paths.REPO_ROOT)}: {old_ver} -> {version}")
                else:
                    log(f"{paths.MARKETPLACE_JSON.relative_to(paths.REPO_ROOT)}: {old_ver} -> {version}")
                break
        if not dry_run:
            paths.MARKETPLACE_JSON.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
