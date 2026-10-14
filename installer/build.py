"""Phase 1: generate platform-filtered content in _dist/."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import paths
from .common import ensure_dir, log, log_section
from .frontmatter import (
    convert_rule_to_mdc,
    rule_applies_to,
    strip_frontmatter,
    strip_platforms_field,
)


def filter_mcp_for_platform(platform: str) -> dict:
    """Load MCP servers filtered by platform."""
    mcp_path = paths.REPO_ROOT / "mcp.json"
    if not mcp_path.exists():
        return {}
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers", {})
    filtered = {}
    for name, config in servers.items():
        platforms = config.get("_platforms")
        if platforms is None or platform in platforms:
            clean = {k: v for k, v in config.items() if k != "_platforms"}
            filtered[name] = clean
    return filtered


def _is_mattpocock_vendored(path: Path) -> bool:
    """Check if a skill/agent path is a symlink into vendor/mattpocock-skills.

    mattpocock/skills ships its own native Claude plugin
    (mattpocock-skills@mattpocock), so on Claude Code these are provided by
    that plugin and must NOT also be distributed by this repo's plugin.
    """
    if not path.is_symlink():
        return False
    vendor_prefix = (paths.REPO_ROOT / "vendor" / "mattpocock-skills").resolve()
    try:
        resolved = path.resolve()
    except OSError:
        return False
    return vendor_prefix in resolved.parents or resolved == vendor_prefix


def _ensure_submodules(dry_run: bool = False) -> None:
    """Initialize git submodules if not already present."""
    vendor_dir = paths.REPO_ROOT / "vendor" / "mattpocock-skills"
    if vendor_dir.exists() and any(vendor_dir.iterdir()):
        return

    if dry_run:
        log("[DRY-RUN] git submodule update --init")
        return

    log("Initializing git submodules...")
    result = subprocess.run(
        ["git", "submodule", "update", "--init"],
        cwd=paths.REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        log("Git submodules initialized")
    else:
        log(f"Warning: submodule init failed: {result.stderr.strip()}")


def _clean_mattpocock_skill_symlinks(dry_run: bool = False) -> None:
    """Remove leftover mattpocock symlinks under skills/.

    Historically build created skills/<name> symlinks into
    vendor/mattpocock-skills/ and deep-copied them into _dist/<platform>/skills/.
    That distribution path is gone now: Claude uses the native
    mattpocock-skills@mattpocock plugin, Codex/Cursor install via
    `install.py manual` (symlinks into ~/.agents/skills/, NOT skills/), and
    skills are no longer copied into _dist at all (all platforms scan the
    repo-root skills/). So any skills/<name> symlink still pointing at the
    mattpocock submodule is stale — left over from an older build on this
    checkout. It MUST be removed so the repo-root skills/ stays clean (the
    single source all platforms scan), and so a stale broken link (if the
    submodule isn't initialized) doesn't trip Cursor's "unsafe source path"
    whole-tree scan.

    Reads the upstream plugin.json skill list (same source `install.py manual`
    uses) so the cleanup stays in sync if upstream adds/removes skills.
    """
    upstream_pj = paths.REPO_ROOT / "vendor" / "mattpocock-skills" / ".claude-plugin" / "plugin.json"
    skills_dir = paths.REPO_ROOT / "skills"
    if not upstream_pj.exists():
        return  # submodule not initialized → no symlinks to clean
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    data = json.loads(upstream_pj.read_text(encoding="utf-8"))
    entries = data.get("skills", [])
    if isinstance(entries, str):
        entries = [entries]
    count = 0
    for entry in entries:
        skill_name = Path(entry).name
        link = skills_dir / skill_name
        if not link.is_symlink():
            continue
        if not _is_mattpocock_vendored(link):
            continue  # not a mattpocock link someone else owns — leave it
        if dry_run:
            log(f"[DRY-RUN] rm stale skills/{skill_name} symlink")
            count += 1
            continue
        link.unlink()
        count += 1
    if count and not dry_run:
        log(f"skills/ stale mattpocock symlinks removed ({count})")


def _ensure_claude_manifest_autoscan(dry_run: bool = False) -> None:
    """Keep the `agents` key out of .claude-plugin/plugin.json.

    Claude Code 2.1.x auto-scans the plugin-root agents/ dir, and a manifest
    `agents` array silently overrides that scan with a resolver that loads
    nothing. Verified 2026-10-08 with two probe plugins sharing one agents/
    dir: the one declaring `"agents": ["./agents/x.md"]` reported Agents (0)
    in `claude plugin details`, the one without the key reported Agents (1).
    `claude plugin validate` passes either way, so the failure is silent.
    Anthropic's own plugins (feature-dev, pr-review-toolkit, plugin-dev, ...)
    ship an agents/ dir with no `agents` key. Build strips the key if it
    returns, so the repo cannot drift back into loading zero agents.
    """
    manifest = paths.REPO_ROOT / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        return
    # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if "agents" not in data:
        return
    del data["agents"]
    if dry_run:
        log(f"[DRY-RUN] strip `agents` from {manifest.relative_to(paths.REPO_ROOT)} "
            f"(Claude auto-scans agents/; the key loads zero agents)")
        return
    manifest.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log(".claude-plugin/plugin.json: stripped `agents` (Claude auto-scans agents/)")


def build_dist(dry_run: bool = False) -> None:
    """Generate platform-filtered content in _dist/."""
    log_section("Building _dist/ (platform-filtered content)")

    _ensure_submodules(dry_run)
    _clean_mattpocock_skill_symlinks(dry_run)

    if not dry_run:
        if paths.DIST.exists():
            # pi-lens-ignore: ast-grep:unchecked-throwing-call-python
            shutil.rmtree(paths.DIST)
        paths.DIST.mkdir()

    for platform in ("cursor", "claude", "codex", "pi"):
        platform_dir = paths.DIST / platform
        ensure_dir(platform_dir, dry_run)

        # Skills and agents are NOT copied into _dist/. The plugin platforms
        # read the repo-root skills/ and agents/ directly (Cursor/Codex
        # manifest: "skills": "./skills/"; Claude: no skills/agents keys →
        # auto-scans plugin-root skills/ and agents/, see
        # _ensure_claude_manifest_autoscan); pi gets symlinks from install_pi.
        # This works because mattpocock/anysearch moved to manual install
        # (~/.agents/skills/ symlinks), so root skills/ holds only committed
        # real files — no vendor symlinks that would break on a fresh clone
        # (no submodule init) and trip Cursor's "unsafe source path" scan.
        # _dist/ now holds only what genuinely differs per platform:
        # mcp.json (_platforms filter), rules (.mdc vs .md), and the
        # global-instructions deploy (CLAUDE.md / AGENTS.md).

        # MCP: filtered per platform (pi excluded — pi gets MCP-equivalent
        # capabilities like playwright via its own extensions, not this repo)
        mcp_servers = {} if platform == "pi" else filter_mcp_for_platform(platform)
        if platform != "pi":
            # Always write the file, even with zero servers. Repo-root .mcp.json
            # is a symlink to _dist/claude/mcp.json and .codex-plugin/plugin.json
            # declares `mcpServers: "./.mcp.json"`, so skipping the write on an
            # empty filter leaves both dangling (hit 2026-10-08: the only server
            # is tagged _platforms: cursor, so _dist/claude/mcp.json never
            # existed). Claude accepts an empty {"mcpServers": {}} plugin file.
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
        # - Codex/pi: no separate rules dir (content embedded in AGENTS.md)
        rules_dir = paths.REPO_ROOT / "rules"
        rules_out = platform_dir / "rules"
        has_rules = False
        if platform not in ("codex", "pi"):
            for rule_file in sorted(rules_dir.rglob("*.md")):
                if not rule_applies_to(rule_file, platform):
                    continue
                has_rules = True
                rel = rule_file.relative_to(rules_dir)
                ensure_dir(rules_out / rel.parent, dry_run)
                if platform == "cursor":
                    dst = rules_out / rel.with_suffix(".mdc")
                    content = convert_rule_to_mdc(rule_file)
                else:
                    dst = rules_out / rel
                    content = strip_platforms_field(rule_file.read_text(encoding="utf-8"))
                if dry_run:
                    log(f"[DRY-RUN] write {dst}")
                else:
                    dst.write_text(content, encoding="utf-8")

        # Global instructions
        gi_src = paths.REPO_ROOT / "global-instructions.md"
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
            elif platform in ("codex", "pi"):
                # Codex/pi AGENTS.md = global instructions + rules/common/.
                # Language conventions live in skills/<lang>-development
                # (loaded on demand), which keeps AGENTS.md under Codex's 32KB
                # default limit. pi loads its copy from ~/.pi/agent/.
                agents_content = gi_content
                common_rules_dir = paths.REPO_ROOT / "rules" / "common"
                rule_sections = []
                if common_rules_dir.exists():
                    for rf in sorted(common_rules_dir.rglob("*.md")):
                        if rule_applies_to(rf, platform):
                            rule_sections.append(strip_frontmatter(rf.read_text(encoding="utf-8")))
                if rule_sections:
                    agents_content += "\n\n# --- Rules ---\n\n" + "\n\n".join(rule_sections)
                dst = platform_dir / "AGENTS.md"
                if dry_run:
                    log(f"[DRY-RUN] write {dst}")
                else:
                    dst.write_text(agents_content, encoding="utf-8")
                    size_kb = len(agents_content.encode("utf-8")) / 1024
                    if platform == "codex" and size_kb > 32:
                        log(f"⚠️  WARNING: Codex AGENTS.md is {size_kb:.1f}KB (exceeds 32KB default limit)")
                        log("  Consider raising project_doc_max_bytes in ~/.codex/config.toml")
                    elif platform == "codex":
                        log(f"Codex AGENTS.md: {size_kb:.1f}KB / 32KB")
                    else:
                        log(f"pi AGENTS.md: {size_kb:.1f}KB")

        if has_rules and not dry_run:
            log(f"_dist/{platform}/rules/ generated")

    # Claude auto-scans the plugin-root agents/ dir; a manifest `agents` key
    # overrides that scan and loads zero agents (probe-verified — see
    # _ensure_claude_manifest_autoscan).
    _ensure_claude_manifest_autoscan(dry_run)
