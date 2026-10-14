"""Command-line entry: platform detection, install orchestration, argparse."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import paths
from .build import _clean_mattpocock_skill_symlinks, _ensure_submodules, build_dist
from .common import log, log_section
from .deploy_claude import install_claude
from .deploy_codex import install_codex
from .deploy_cursor import install_cursor
from .deploy_pi import _remove_legacy_agents_skill_links, install_pi
from .third_party import install_manual_skills
from .version import _bump_version, _get_current_version, set_version


def detect_platforms(home: Path = paths.HOME) -> dict[str, tuple[bool, str]]:
    """Detect which agent platforms are present on this machine.

    Each platform is detected by the most authoritative available signal:
      - claude / codex / pi: CLI on PATH (the same binary the installer uses),
        falling back to the user-level config dir (~/.claude, ~/.codex, ~/.pi).
      - cursor: CLI on PATH, then ~/.cursor config dir, then the macOS app
        bundle (Cursor's `cursor` CLI is opt-in via the Command Palette, so
        the .app is the strongest signal — only checked on sys.platform=darwin).

    Returns a dict with all 4 keys regardless of detection outcome, so callers
    can log a uniform detection report. Each value is `(installed, reason)`:
    reason names the signal that triggered the decision (positive or negative).
    """
    results: dict[str, tuple[bool, str]] = {}

    claude_cli = shutil.which("claude")
    if claude_cli:
        results["claude"] = (True, f"claude CLI on PATH: {claude_cli}")
    elif paths.CLAUDE_HOME.exists():
        results["claude"] = (True, f"config dir: {paths.CLAUDE_HOME}")
    else:
        results["claude"] = (False, "no claude CLI on PATH and ~/.claude not found")

    codex_cli = shutil.which("codex")
    if codex_cli:
        results["codex"] = (True, f"codex CLI on PATH: {codex_cli}")
    elif paths.CODEX_HOME.exists():
        results["codex"] = (True, f"config dir: {paths.CODEX_HOME}")
    else:
        results["codex"] = (False, "no codex CLI on PATH and ~/.codex not found")

    cursor_cli = shutil.which("cursor")
    if cursor_cli:
        results["cursor"] = (True, f"cursor CLI on PATH: {cursor_cli}")
    elif paths.CURSOR_HOME.exists():
        results["cursor"] = (True, f"config dir: {paths.CURSOR_HOME}")
    elif sys.platform == "darwin":
        for app in (Path("/Applications/Cursor.app"), home / "Applications" / "Cursor.app"):
            if app.exists():
                results["cursor"] = (True, f"app bundle: {app}")
                break
        else:
            results["cursor"] = (False, "no cursor CLI on PATH, ~/.cursor not found, "
                                       "and /Applications/Cursor.app missing")
    else:
        results["cursor"] = (False, "no cursor CLI on PATH and ~/.cursor not found")

    pi_cli = shutil.which("pi")
    if pi_cli:
        results["pi"] = (True, f"pi CLI on PATH: {pi_cli}")
    elif paths.PI_AGENT_HOME.exists():
        results["pi"] = (True, f"config dir: {paths.PI_AGENT_HOME}")
    else:
        results["pi"] = (False, "no pi CLI on PATH and ~/.pi/agent not found")

    return results


def _do_install(platform: str, dry_run: bool) -> None:
    """Run platform installers, then install third-party manual skills.

    Manual (symlink-installed) skills declared in third-party.json's
    `install` objects are installed once after the platform installers,
    regardless of --platform. They target user-level dirs
    (~/.agents/skills/, ~/.claude/skills/) that are shared across platforms,
    so a single pass covers all of them. Use `install.py manual <name>`
    to reinstall just one skill.

    Platform detection: `detect_platforms()` decides what is on this machine.
      - `--platform all` (default): installs only detected platforms, logging
        the reason for any skipped platform. Prevents polluting home with
        ~/.codex / ~/.cursor / ~/.pi on a machine that lacks them.
      - `--platform <name>`: errors out (SystemExit) if that platform is not
        detected, since an explicit request almost always means a typo or a
        real install gap — fail loud rather than silently writing config
        into a directory the tool will never read.
    """
    _ensure_submodules(dry_run)
    _clean_mattpocock_skill_symlinks(dry_run)
    # Runs on every install, not only for pi: the legacy links make Codex
    # double-load self-owned skills even where pi is no longer detected.
    _remove_legacy_agents_skill_links(dry_run)

    detection = detect_platforms()
    detected = {name for name, (ok, _reason) in detection.items() if ok}

    log_section("Platform detection")
    for name, (ok, reason) in detection.items():
        marker = "✓" if ok else "✗"
        log(f"{marker} {name}: {reason}")

    platforms = {
        "claude": install_claude,
        "codex": install_codex,
        "cursor": install_cursor,
        "pi": install_pi,
    }
    if platform == "all":
        for name, installer in platforms.items():
            if name in detected:
                installer(dry_run)
            else:
                log(f"[skip {name}] {detection[name][1]}")
    else:
        if platform not in detected:
            _, reason = detection[platform]
            raise SystemExit(
                f"platform '{platform}' not detected on this machine ({reason}). "
                f"Install it, or omit --platform to default to detected platforms only."
            )
        platforms[platform](dry_run)
    # Install all third-party manual skills once (not per-platform — they
    # link into shared user-level dirs). Same third-party.json source as
    # `install.py manual`, so this is the single source of truth for
    # third-party skill deployment; no separate command needed.
    install_manual_skills(name=None, dry_run=dry_run)


def main() -> None:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )

    parser = argparse.ArgumentParser(
        description="Unified AI agent assets: build plugin content and/or install to platforms",
        parents=[parent],
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build", parents=[parent], help="Only regenerate _dist/ (plugin content)")

    install_parser = sub.add_parser("install", parents=[parent], help="Install platform plugins + AGENTS.md/rules + third-party skills")
    install_parser.add_argument(
        "--platform",
        choices=["claude", "codex", "cursor", "pi", "all"],
        default="all",
        help="Target platform (default: all)",
    )

    version_parser = sub.add_parser("version", parents=[parent], help="Set or bump plugin version")
    version_parser.add_argument(
        "new_version",
        nargs="?",
        help="Explicit version (e.g. 1.2.0)",
    )
    version_parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Bump version part instead of setting explicitly",
    )

    manual_parser = sub.add_parser(
        "manual",
        parents=[parent],
        help="Reinstall one third-party (symlink) skill from third-party.json. "
        "`install` already runs this for all skills; use `manual <name>` "
        "to reinstall just one.",
    )
    manual_parser.add_argument(
        "name",
        nargs="?",
        help="Skill name (the `name` field in third-party.json). "
        "If omitted, install every plugin with an `install` object "
        "(same as what `install` already does).",
    )

    parser.add_argument(
        "--platform",
        choices=["claude", "codex", "cursor", "pi", "all"],
        default="all",
        help="Target platform (default: all, used when no subcommand given)",
    )

    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Unified AI Agent Assets Installer                      ║")
    print("╚══════════════════════════════════════════════════════════╝")

    if args.dry_run:
        print("\n⚠️  DRY-RUN MODE - No changes will be made\n")

    if args.command == "build":
        build_dist(args.dry_run)
    elif args.command == "install":
        _do_install(args.platform, args.dry_run)
    elif args.command == "version":
        if args.new_version:
            set_version(args.new_version, args.dry_run)
        elif args.bump:
            current = _get_current_version()
            new_ver = _bump_version(current, args.bump)
            set_version(new_ver, args.dry_run)
        else:
            print(f"  Current version: {_get_current_version()}")
    elif args.command == "manual":
        install_manual_skills(getattr(args, "name", None), args.dry_run)
    else:
        build_dist(args.dry_run)
        _do_install(args.platform, args.dry_run)

    log_section("Done")
    if not args.dry_run:
        print("\nNext steps:")
        print("  1. Restart agents to pick up changes")
    else:
        print("\nRe-run without --dry-run to apply.")
