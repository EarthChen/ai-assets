#!/usr/bin/env python3
"""
Unified AI agent assets installer.

Two-phase deployment:
  Phase 1 (build): Generate platform-filtered content in _dist/
  Phase 2 (deploy): Install plugin symlinks + handle non-plugin assets

Plugin systems handle:
  - Cursor: rules, skills, MCP (from _dist/cursor/)
  - Claude Code: skills, MCP (from _dist/claude/)
  - Codex: skills (from _dist/codex/)

Script handles (things plugins can't do):
  - Claude Code: CLAUDE.md, rules → ~/.claude/rules/common/
  - Codex: AGENTS.md + rules appended, approval rules
  - All: plugin symlinks, ~/.agents/skills/ symlinks

Usage:
    uv run install.py [--platform claude|codex|cursor|all] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOME = Path.home()
DIST = REPO_ROOT / "_dist"

CLAUDE_HOME = HOME / ".claude"
CODEX_HOME = HOME / ".codex"
CURSOR_HOME = HOME / ".cursor"
AGENTS_HOME = HOME / ".agents"


def log(msg: str) -> None:
    print(f"  → {msg}")


def log_section(msg: str) -> None:
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


def ensure_dir(path: Path, dry_run: bool = False) -> None:
    if not path.exists():
        if dry_run:
            log(f"[DRY-RUN] mkdir {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path, dry_run: bool = False) -> None:
    ensure_dir(dst.parent, dry_run)
    if dry_run:
        log(f"[DRY-RUN] copy {src.name} -> {dst}")
    else:
        shutil.copy2(src, dst)
        log(f"Copied {src.name} -> {dst}")


def create_symlink(src: Path, dst: Path, dry_run: bool = False) -> None:
    ensure_dir(dst.parent, dry_run)
    if dst.is_symlink() or dst.exists():
        if dry_run:
            log(f"[DRY-RUN] relink {dst}")
        else:
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
    if dry_run:
        log(f"[DRY-RUN] symlink {dst} -> {src}")
    else:
        dst.symlink_to(src)
        log(f"Symlinked {dst.name} -> {src}")


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter. Returns (metadata_dict, body_content)."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    fm_text = content[3:end].strip()
    body = content[end + 3:].lstrip("\n")

    metadata: dict = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            elif val.lower() in ("true", "false"):
                val = val.lower() == "true"
            metadata[key] = val
    return metadata, body


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content."""
    _, body = parse_frontmatter(content)
    return body


def rule_applies_to(rule_path: Path, platform: str) -> bool:
    """Check if a rule applies to the given platform."""
    content = rule_path.read_text(encoding="utf-8")
    metadata, _ = parse_frontmatter(content)
    platforms = metadata.get("platforms")
    if platforms is None:
        return True
    if isinstance(platforms, list):
        return platform in platforms
    return True


def convert_rule_to_mdc(src: Path) -> str:
    """Ensure rule file has .mdc-compatible format (YAML frontmatter present)."""
    content = src.read_text(encoding="utf-8")
    if content.startswith("---"):
        return content
    name = src.stem
    return f'---\ndescription: "{name}"\nalwaysApply: true\n---\n{content}'


def filter_mcp_for_platform(platform: str) -> dict:
    """Load MCP servers filtered by platform."""
    mcp_path = REPO_ROOT / "mcp.json"
    if not mcp_path.exists():
        return {}
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers", {})
    filtered = {}
    for name, config in servers.items():
        platforms = config.get("_platforms")
        if platforms is None or platform in platforms:
            clean = {k: v for k, v in config.items() if k != "_platforms"}
            filtered[name] = clean
    return filtered


def _asset_applies_to(path: Path, platform: str) -> bool:
    """Check if a skill directory or agent file applies to the given platform."""
    # For skill dirs, check SKILL.md frontmatter
    if path.is_dir():
        skill_md = path / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            metadata, _ = parse_frontmatter(content)
            platforms = metadata.get("platforms")
            if platforms and isinstance(platforms, list):
                return platform in platforms
        return True
    # For agent .md files, check frontmatter
    if path.suffix == ".md":
        content = path.read_text(encoding="utf-8")
        metadata, _ = parse_frontmatter(content)
        platforms = metadata.get("platforms")
        if platforms and isinstance(platforms, list):
            return platform in platforms
    return True


def _has_platform_filtered_content(src_dir: Path, platform: str) -> bool:
    """Check if any item in the directory has platform restrictions."""
    if not src_dir.exists():
        return False
    for item in src_dir.iterdir():
        if not _asset_applies_to(item, platform):
            return True
    return False


# ─── Phase 1: Build _dist/ ─────────────────────────────────────────────────────

def build_dist(dry_run: bool = False) -> None:
    """Generate platform-filtered content in _dist/."""
    log_section("Building _dist/ (platform-filtered content)")

    if not dry_run:
        if DIST.exists():
            shutil.rmtree(DIST)
        DIST.mkdir()

    for platform in ("cursor", "claude", "codex"):
        platform_dir = DIST / platform
        ensure_dir(platform_dir, dry_run)

        # Skills: symlink to shared skills/ (or filtered if platform-specific)
        skills_src = REPO_ROOT / "skills"
        skills_out = platform_dir / "skills"
        if _has_platform_filtered_content(skills_src, platform):
            # Some skills have platform restrictions, build filtered directory
            ensure_dir(skills_out, dry_run)
            for skill_dir in skills_src.iterdir():
                if not skill_dir.is_dir():
                    continue
                if not _asset_applies_to(skill_dir, platform):
                    continue
                dst = skills_out / skill_dir.name
                if dry_run:
                    log(f"[DRY-RUN] symlink {dst}")
                else:
                    dst.symlink_to(Path(f"../../../skills/{skill_dir.name}"))
            if not dry_run:
                log(f"_dist/{platform}/skills (filtered)")
        else:
            # No filtering needed, direct symlink
            if dry_run:
                log(f"[DRY-RUN] symlink {skills_out} -> ../../skills")
            else:
                ensure_dir(platform_dir)
                skills_out.symlink_to(Path("../../skills"))
                log(f"_dist/{platform}/skills -> ../../skills")

        # Agents: for platforms that support it via plugin
        if platform in ("cursor", "claude"):
            agents_src = REPO_ROOT / "agents"
            agents_out = platform_dir / "agents"
            if agents_src.exists():
                if _has_platform_filtered_content(agents_src, platform):
                    ensure_dir(agents_out, dry_run)
                    for agent_file in agents_src.glob("*.md"):
                        if not _asset_applies_to(agent_file, platform):
                            continue
                        dst = agents_out / agent_file.name
                        if dry_run:
                            log(f"[DRY-RUN] symlink {dst}")
                        else:
                            dst.symlink_to(Path(f"../../../agents/{agent_file.name}"))
                    if not dry_run:
                        log(f"_dist/{platform}/agents (filtered)")
                else:
                    if dry_run:
                        log(f"[DRY-RUN] symlink {agents_out} -> ../../agents")
                    else:
                        agents_out.symlink_to(Path("../../agents"))
                        log(f"_dist/{platform}/agents -> ../../agents")

        # MCP: filtered per platform
        mcp_servers = filter_mcp_for_platform(platform)
        if mcp_servers:
            mcp_out = platform_dir / "mcp.json"
            content = json.dumps({"mcpServers": mcp_servers}, indent=2, ensure_ascii=False)
            if dry_run:
                log(f"[DRY-RUN] write {mcp_out} ({len(mcp_servers)} servers)")
            else:
                mcp_out.write_text(content + "\n", encoding="utf-8")
                log(f"_dist/{platform}/mcp.json ({len(mcp_servers)} servers)")

        # Rules: filtered per platform
        # - Cursor: .mdc files in rules/
        # - Claude: .md files in rules/ (for script to deploy)
        # - Codex: no separate rules dir (content embedded in AGENTS.md)
        rules_dir = REPO_ROOT / "rules"
        rules_out = platform_dir / "rules"
        has_rules = False
        if platform != "codex":
            for rule_file in sorted(rules_dir.glob("*.md")):
                if not rule_applies_to(rule_file, platform):
                    continue
                has_rules = True
                ensure_dir(rules_out, dry_run)
                if platform == "cursor":
                    dst = rules_out / f"{rule_file.stem}.mdc"
                    content = convert_rule_to_mdc(rule_file)
                else:
                    dst = rules_out / rule_file.name
                    content = strip_frontmatter(rule_file.read_text(encoding="utf-8"))
                if dry_run:
                    log(f"[DRY-RUN] write {dst}")
                else:
                    dst.write_text(content, encoding="utf-8")

        # Global instructions
        gi_src = REPO_ROOT / "global-instructions.md"
        if gi_src.exists():
            gi_content = gi_src.read_text(encoding="utf-8")
            if platform == "cursor":
                # Include as a rule for Cursor
                ensure_dir(rules_out, dry_run)
                has_rules = True
                mdc = f'---\ndescription: "Global instructions: language, tech stack, conventions"\nalwaysApply: true\n---\n{gi_content}'
                dst = rules_out / "global-instructions.mdc"
                if dry_run:
                    log(f"[DRY-RUN] write {dst}")
                else:
                    dst.write_text(mdc, encoding="utf-8")
            elif platform == "claude":
                dst = platform_dir / "CLAUDE.md"
                if dry_run:
                    log(f"[DRY-RUN] write {dst}")
                else:
                    dst.write_text(gi_content, encoding="utf-8")
            elif platform == "codex":
                # Codex AGENTS.md = global instructions + all applicable rules
                codex_content = gi_content
                rules_dir_src = REPO_ROOT / "rules"
                rule_sections = []
                for rf in sorted(rules_dir_src.glob("*.md")):
                    if rule_applies_to(rf, "codex"):
                        rule_sections.append(strip_frontmatter(rf.read_text(encoding="utf-8")))
                if rule_sections:
                    codex_content += "\n\n# --- Rules ---\n\n" + "\n\n".join(rule_sections)
                dst = platform_dir / "AGENTS.md"
                if dry_run:
                    log(f"[DRY-RUN] write {dst}")
                else:
                    dst.write_text(codex_content, encoding="utf-8")

        if has_rules and not dry_run:
            log(f"_dist/{platform}/rules/ generated")


# ─── Phase 2: Deploy ───────────────────────────────────────────────────────────

def install_claude(dry_run: bool = False) -> None:
    log_section("Deploying Claude Code")

    # 1. Plugin symlink (plugin loads: skills, MCP from _dist/claude/)
    plugin_dir = CLAUDE_HOME / "plugins" / "local" / "earthchen-ai-assets"
    create_symlink(REPO_ROOT, plugin_dir, dry_run)
    log("Plugin provides: skills, MCP (filtered)")

    # 2. CLAUDE.md (plugin can't handle)
    dist_claude_md = DIST / "claude" / "CLAUDE.md"
    dst_claude_md = CLAUDE_HOME / "CLAUDE.md"
    if dist_claude_md.exists():
        if dry_run:
            log(f"[DRY-RUN] write {dst_claude_md}")
        else:
            ensure_dir(CLAUDE_HOME)
            shutil.copy2(dist_claude_md, dst_claude_md)
            log(f"_dist/claude/CLAUDE.md -> {dst_claude_md}")

    # 3. Rules (plugin can't distribute rules for Claude Code)
    rules_src = DIST / "claude" / "rules"
    dst_rules = CLAUDE_HOME / "rules" / "common"
    if rules_src.exists():
        ensure_dir(dst_rules, dry_run)
        for rule_file in sorted(rules_src.glob("*.md")):
            dst = dst_rules / rule_file.name
            if dry_run:
                log(f"[DRY-RUN] write {dst}")
            else:
                shutil.copy2(rule_file, dst)
                log(f"Rule {rule_file.name} -> {dst}")

    # 4. Shared skills -> ~/.agents/skills/
    _deploy_shared_skills(dry_run)


def install_codex(dry_run: bool = False) -> None:
    log_section("Deploying Codex")

    # 1. Plugin symlink (plugin loads: skills from _dist/codex/)
    plugin_dir = CODEX_HOME / "plugins" / "local" / "earthchen-ai-assets"
    create_symlink(REPO_ROOT, plugin_dir, dry_run)
    log("Plugin provides: skills")

    # 2. AGENTS.md (plugin can't handle, pre-built in _dist/)
    dist_agents = DIST / "codex" / "AGENTS.md"
    dst_agents = CODEX_HOME / "AGENTS.md"
    if dist_agents.exists():
        if dry_run:
            log(f"[DRY-RUN] write {dst_agents}")
        else:
            ensure_dir(CODEX_HOME)
            shutil.copy2(dist_agents, dst_agents)
            log(f"_dist/codex/AGENTS.md -> {dst_agents}")

    # 3. Command approval rules
    approval_src = REPO_ROOT / "rules" / "codex-approval.rules"
    approval_dst = CODEX_HOME / "rules" / "default.rules"
    if approval_src.exists():
        copy_file(approval_src, approval_dst, dry_run)

    # 4. Shared skills -> ~/.agents/skills/
    _deploy_shared_skills(dry_run)


def install_cursor(dry_run: bool = False) -> None:
    log_section("Deploying Cursor")

    # Plugin handles everything (rules, skills, MCP from _dist/cursor/)
    # Script only creates the symlink
    plugin_dir = CURSOR_HOME / "plugins" / "local" / "earthchen-ai-assets"
    create_symlink(REPO_ROOT, plugin_dir, dry_run)
    log("Plugin provides: rules, skills, MCP (all via native plugin system)")

    # Shared skills -> ~/.agents/skills/
    _deploy_shared_skills(dry_run)


def _deploy_shared_skills(dry_run: bool = False) -> None:
    """Deploy skills to ~/.agents/skills/ via symlinks."""
    skills_dir = REPO_ROOT / "skills"
    dst_skills = AGENTS_HOME / "skills"
    ensure_dir(dst_skills, dry_run)

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        dst = dst_skills / skill_dir.name
        create_symlink(skill_dir.resolve(), dst, dry_run)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install unified AI agent assets to all platforms"
    )
    parser.add_argument(
        "--platform",
        choices=["claude", "codex", "cursor", "all"],
        default="all",
        help="Target platform (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Unified AI Agent Assets Installer                      ║")
    print("╚══════════════════════════════════════════════════════════╝")

    if args.dry_run:
        print("\n⚠️  DRY-RUN MODE - No changes will be made\n")

    # Phase 1: Build _dist/
    build_dist(args.dry_run)

    # Phase 2: Deploy
    platforms = {
        "claude": install_claude,
        "codex": install_codex,
        "cursor": install_cursor,
    }

    if args.platform == "all":
        for installer in platforms.values():
            installer(args.dry_run)
    else:
        platforms[args.platform](args.dry_run)

    log_section("Done")
    if not args.dry_run:
        print("\nNext steps:")
        print("  1. Install third-party plugins (see third-party.json)")
        print("  2. Restart agents to pick up changes")
    else:
        print("\nRe-run without --dry-run to apply.")


if __name__ == "__main__":
    main()
