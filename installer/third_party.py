"""third-party.json loading and manual (symlink-installed) third-party skills."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from . import paths
from .common import create_symlink, log, log_section


def _load_third_party_plugins() -> list[dict]:
    """Load third-party plugin config from third-party.json."""
    if not paths.THIRD_PARTY_JSON.exists():
        return []
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    data = json.loads(paths.THIRD_PARTY_JSON.read_text(encoding="utf-8"))
    return data.get("plugins", [])


# ─── manual skills (symlink-installed, NOT plugin-distributed) ─────────────────
#
# Skills that bypass plugin distribution: they need runtime files
# (runtime.conf, .env) to persist across sessions, but plugin cache
# (~/.claude/plugins/cache/.../) is a read-only snapshot overwritten on every
# `ref: main` pull — any file the agent writes there is lost on the next
# session. So these skills install as user-level symlinks pointing into
# vendor/, where each platform follows the symlink and persistent files
# survive. The submodules stay out of build/_dist (skills aren't copied into
# _dist at all anymore — all platforms scan the repo-root skills/), so they
# never enter any platform's plugin tree.
#
# Which skills install this way, their source submodule, and the user-level
# paths to symlink are declared in third-party.json as a top-level `install`
# object per plugin:
#   "install": {"source": "vendor/<name>", "links": ["~/.claude/skills/<name>", ...]}
# `links` entries use ~ which is expanded with Path.expanduser(). Platform-
# specific caveats live in each platform's `note` field. This loader is
# generic: adding a second manual skill means adding a third-party.json entry
# with an `install` object, no code change here.
#
# `generate` has two skill-discovery forms (mutually exclusive):
#   - {from, field, link_dir}: read <source>/<from> JSON, take <field> as a
#     list of relative paths (e.g. mattpocock's plugin.json "skills").
#   - {scan_dir, link_dir}: scan <source>/<scan_dir> for subdirs containing
#     a SKILL.md — for multi-skill repos whose manifest has no skill list
#     (e.g. understand-anything: skills live under
#     understand-anything-plugin/skills/<name>/SKILL.md).
# `extra_links` (optional, list of link_dirs): each discovered skill is also
# symlinked into these dirs in addition to link_dir — lets one generate
# entry cover multiple platform dirs (e.g. ~/.agents/skills + ~/.claude/skills).

def _expand_install_links(install: dict, source: Path) -> list[tuple[Path, Path]]:
    """Resolve an `install` object into (link_path, target_path) pairs.

    Two forms, mutually exclusive:
    - `links`: explicit list of user-level paths (each → source root).
      For single-skill repos whose root IS the skill root (e.g. anysearch).
    - `generate`: discover skills then symlink each into one or more dirs.
      Two skill-discovery sub-forms (mutually exclusive):
      - {from, field, link_dir}: read <source>/<from> JSON, take <field> as
        a list of relative paths like "./skills/engineering/tdd" (e.g.
        the skill list in mattpocock's .claude-plugin/plugin.json).
      - {scan_dir, link_dir}: scan <source>/<scan_dir> for subdirs
        containing a SKILL.md — for multi-skill repos whose manifest carries
        no skill list (e.g. understand-anything, whose skills live under
        understand-anything-plugin/skills/<name>/SKILL.md).
      `extra_links` (optional, list of link_dirs): each discovered skill is
      also symlinked into these dirs, so one generate entry covers multiple
      platform dirs (e.g. ~/.agents/skills + ~/.claude/skills).
    """
    if "links" in install and "generate" in install:
        raise ValueError("install: use `links` OR `generate`, not both")
    if "links" in install:
        return [(Path(p).expanduser(), source) for p in install["links"]]
    if "generate" in install:
        gen = install["generate"]
        link_dir = Path(gen["link_dir"]).expanduser()
        extra_dirs = [Path(p).expanduser() for p in gen.get("extra_links", [])]
        # Resolve the list of (skill_name, source_subpath) pairs to link.
        if "from" in gen and "scan_dir" in gen:
            raise ValueError("generate: use `from`+`field` OR `scan_dir`, not both")
        discovered = []  # [(skill_name, source_subpath), ...]
        if "scan_dir" in gen:
            scan_root = source / gen["scan_dir"]
            for child in sorted(scan_root.iterdir()):
                if not child.is_dir():
                    continue
                # Skip non-skill dirs (e.g. shared/ lib code without SKILL.md).
                if not (child / "SKILL.md").is_file():
                    continue
                sub = str(child.relative_to(source))
                discovered.append((child.name, sub))
        else:  # "from" + "field"
            manifest = source / gen["from"]
            # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
            data = json.loads(manifest.read_text(encoding="utf-8"))
            entries = data.get(gen["field"], [])
            if isinstance(entries, str):
                entries = [entries]
            for entry in entries:
                # entry looks like "./skills/engineering/tdd"
                sub = entry[2:] if entry.startswith("./") else entry
                discovered.append((Path(sub).name, sub))
        pairs = []
        for skill_name, sub in discovered:
            for d in [link_dir, *extra_dirs]:
                pairs.append((d / skill_name, source / sub))
        return pairs
    return []


def _manual_skills() -> list[dict]:
    """Plugins in third-party.json that declare an `install` object.

    Each returned dict: {name, source (Path), pairs (list[(link, target)])}.
    Plugins with a string `install_cmd` per-platform are skipped — they're not
    symlink-installed by this command.
    """
    result = []
    for plugin in _load_third_party_plugins():
        install = plugin.get("install")
        if not isinstance(install, dict):
            continue
        source = paths.REPO_ROOT / install["source"]
        pairs = _expand_install_links(install, source)
        result.append({"name": plugin["name"], "source": source, "pairs": pairs})
    return result


def install_manual_skills(name: str | None, dry_run: bool = False) -> None:
    """Install manual (symlink) skills declared in third-party.json.

    For each plugin with an `install` object (or just the named one), ensure
    the source submodule is initialized, then create an absolute symlink for
    each resolved (link, target) pair. Absolute links survive same-machine
    repo moves; these user-level skill dirs are machine-local anyway.
    """
    skills = _manual_skills()
    if name is not None:
        skills = [s for s in skills if s["name"] == name]
        if not skills:
            log(f"ERROR: no manual skill named '{name}' in third-party.json "
                f"(look for plugins with an `install` object)")
            return
    if not skills:
        log("No manual skills declared in third-party.json "
            "(no plugin has an `install` object)")
        return

    log_section(f"Installing manual skills ({len(skills)}): "
                f"{', '.join(s['name'] for s in skills)}")

    for skill in skills:
        src, pairs = skill["source"], skill["pairs"]
        # Ensure the submodule is initialized before symlinking into it. The
        # source root may or may not have a SKILL.md (anysearch does,
        # mattpocock doesn't — its skills live in subdirs), so just check the
        # dir is non-empty.
        if not src.is_dir() or not any(src.iterdir()):
            rel = src.relative_to(paths.REPO_ROOT)
            if dry_run:
                log(f"[DRY-RUN] git submodule update --init {rel}")
            else:
                log(f"[{skill['name']}] initializing submodule {rel}...")
                result = subprocess.run(
                    ["git", "submodule", "update", "--init", str(rel)],
                    cwd=paths.REPO_ROOT, capture_output=True, text=True,
                )
                if result.returncode != 0:
                    log(f"ERROR: submodule init failed: {result.stderr.strip()}")
                    continue

        log(f"[{skill['name']}] {len(pairs)} symlink(s)")
        for link, target in pairs:
            create_symlink(target.resolve(), link, dry_run)

    if dry_run:
        return
    log("Manual skills installed. Each symlink points at its vendor submodule,")
    log("so `git submodule update --remote <path>` (then re-pin to a tag) flows")
    log("to all platforms at once. Caveats per platform are in third-party.json")
    log("under each platform's `note`.")
