#!/usr/bin/env python3
"""
Unified AI agent assets installer.

Two-phase deployment:
  Phase 1 (build): Generate platform-filtered content in _dist/
  Phase 2 (deploy): Install plugin symlinks + handle non-plugin assets

Plugin systems handle:
  - Cursor: rules, skills, agents, MCP (from _dist/cursor/)
  - Claude Code: skills, agents, MCP (from _dist/claude/)
  - Codex: skills, MCP (from _dist/codex/)

Script handles (things plugins can't do):
  - Claude Code: CLAUDE.md, rules → ~/.claude/rules/common/
  - Codex: AGENTS.md
  - All: plugin symlinks

Usage:
    uv run install.py                         # build + install (all platforms)
    uv run install.py build                   # only regenerate _dist/
    uv run install.py install --platform X    # only install symlinks
    uv run install.py version 1.2.0           # set version across all plugins
    uv run install.py version --bump patch    # bump version (major/minor/patch)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
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
    """Parse YAML frontmatter. Returns (metadata_dict, body_content).

    Handles both inline and multi-line YAML list syntax:
      globs: ["**/*.ts", "**/*.tsx"]   # inline list
      paths:                            # multi-line list
        - "**/*.java"
    """
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    fm_text = content[3:end].strip()
    body = content[end + 3:].lstrip("\n")

    metadata: dict = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in fm_text.splitlines():
        stripped = line.strip()
        # Multi-line list item: "  - value"
        if stripped.startswith("- ") and current_key is not None:
            item = stripped[2:].strip().strip("\"'")
            if current_list is None:
                current_list = []
            current_list.append(item)
            continue

        # Flush pending list
        if current_key is not None and current_list is not None:
            metadata[current_key] = current_list
            current_key = None
            current_list = None

        if ":" not in stripped:
            continue

        key, val = stripped.split(":", 1)
        key = key.strip()
        val = val.strip()

        if not val:
            # Empty value — next lines may be list items
            current_key = key
            current_list = []
        elif val.startswith("[") and val.endswith("]"):
            metadata[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
        elif val.lower() in ("true", "false"):
            metadata[key] = val.lower() == "true"
        else:
            metadata[key] = val.strip("\"'")

    # Flush final pending list
    if current_key is not None and current_list is not None:
        metadata[current_key] = current_list

    return metadata, body


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content."""
    _, body = parse_frontmatter(content)
    return body


def strip_platforms_field(content: str) -> str:
    """Convert rule to Claude Code format: normalize to paths CSV, remove platforms.

    Claude Code specifics:
      - Official field is 'paths' (not 'globs') for conditional loading
      - Must use CSV string format (not YAML arrays) due to parser bugs
      - Must include alwaysApply: false for lazy loading
      - 'platforms' is build-time only, removed from output
    """
    metadata, body = parse_frontmatter(content)
    if not metadata:
        return content

    # Remove platforms (build-time only field)
    cleaned = {k: v for k, v in metadata.items() if k != "platforms"}
    if not cleaned:
        return body

    # Normalize globs → paths for Claude Code (official field)
    if "globs" in cleaned and "paths" not in cleaned:
        cleaned["paths"] = cleaned.pop("globs")
    elif "globs" in cleaned and "paths" in cleaned:
        del cleaned["globs"]

    # Reconstruct frontmatter with Claude Code compatible format
    lines: list[str] = []
    for key, val in cleaned.items():
        if isinstance(val, bool):
            lines.append(f"{key}: {str(val).lower()}")
        elif isinstance(val, list):
            if key == "paths":
                # Claude Code requires CSV string, not YAML array
                csv_val = ", ".join(val)
                lines.append(f"paths: {csv_val}")
            else:
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f'  - "{item}"')
        else:
            if key == "paths":
                # Already a string, keep as-is
                lines.append(f"paths: {val}")
            else:
                lines.append(f'{key}: "{val}"')

    # Ensure alwaysApply: false if paths present (required for lazy loading)
    if "paths" in cleaned and "alwaysApply" not in cleaned:
        lines.append("alwaysApply: false")

    fm = "\n".join(lines)
    return f"---\n{fm}\n---\n{body}"


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
    """Convert a rule to Cursor .mdc format with proper frontmatter translation.

    Translates platform-agnostic frontmatter to Cursor-specific fields:
      - paths → globs (Cursor uses 'globs', not 'paths')
      - Removes 'platforms' field (build-time only, not Cursor-native)
      - Ensures alwaysApply is set appropriately
    """
    content = src.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)

    if not metadata:
        name = src.stem
        return f'---\ndescription: "{name}"\nalwaysApply: true\n---\n{body}'

    # Build Cursor-compatible frontmatter
    mdc_fields: list[str] = []

    if "description" in metadata:
        desc = metadata["description"]
        mdc_fields.append(f'description: "{desc}"')

    # Translate paths → globs for Cursor
    globs = metadata.get("globs") or metadata.get("paths")
    if globs:
        if isinstance(globs, list):
            globs_str = json.dumps(globs)
        else:
            globs_str = f'["{globs}"]'
        mdc_fields.append(f"globs: {globs_str}")

    # alwaysApply: default to true unless globs/paths present
    if "alwaysApply" in metadata:
        mdc_fields.append(f"alwaysApply: {str(metadata['alwaysApply']).lower()}")
    elif globs:
        mdc_fields.append("alwaysApply: false")
    else:
        mdc_fields.append("alwaysApply: true")

    fm = "\n".join(mdc_fields)
    return f"---\n{fm}\n---\n{body}"


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


def _is_mattpocock_vendored(path: Path) -> bool:
    """Check if a skill/agent path is a symlink into vendor/mattpocock-skills.

    mattpocock/skills ships its own native Claude plugin
    (mattpocock-skills@mattpocock), so on Claude Code these are provided by
    that plugin and must NOT also be distributed by this repo's plugin.
    """
    if not path.is_symlink():
        return False
    vendor_prefix = (REPO_ROOT / "vendor" / "mattpocock-skills").resolve()
    try:
        resolved = path.resolve()
    except OSError:
        return False
    return vendor_prefix in resolved.parents or resolved == vendor_prefix


def _asset_applies_to(path: Path, platform: str) -> bool:
    """Check if a skill directory or agent file applies to the given platform."""
    # Claude Code: mattpocock skills are provided by their own native plugin,
    # so exclude them from this repo's Claude distribution. This must run
    # before the is_dir() branch below, which follows the symlink into the
    # vendor and reads SKILL.md (no platforms field → would return True).
    if platform == "claude" and _is_mattpocock_vendored(path):
        return False
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

def _ensure_submodules(dry_run: bool = False) -> None:
    """Initialize git submodules if not already present."""
    vendor_dir = REPO_ROOT / "vendor" / "mattpocock-skills"
    if vendor_dir.exists() and any(vendor_dir.iterdir()):
        return

    if dry_run:
        log("[DRY-RUN] git submodule update --init")
        return

    log("Initializing git submodules...")
    result = subprocess.run(
        ["git", "submodule", "update", "--init"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        log("Git submodules initialized")
    else:
        log(f"Warning: submodule init failed: {result.stderr.strip()}")


def _ensure_mattpocock_skill_symlinks(dry_run: bool = False) -> None:
    """Create skills/<name> symlinks for vendored mattpocock skills.

    These symlinks point into vendor/mattpocock-skills/ (a git submodule) and
    are generated at build time rather than committed. Committing them is
    unsafe for Cursor: a marketplace clone does not `git submodule update
    --init`, so the symlinks ship as broken links with a `../vendor/...`
    target. Cursor's install-time whole-tree safety scan rejects the whole
    plugin ("unresolved or unsafe source path"). The skill set is read from
    the upstream plugin.json so it stays in sync with the submodule.
    """
    upstream_pj = REPO_ROOT / "vendor" / "mattpocock-skills" / ".claude-plugin" / "plugin.json"
    skills_dir = REPO_ROOT / "skills"
    if not upstream_pj.exists():
        log("Skipping mattpocock skill symlinks (submodule not initialized)")
        return
    data = json.loads(upstream_pj.read_text(encoding="utf-8"))
    entries = data.get("skills", [])
    if isinstance(entries, str):
        entries = [entries]
    ensure_dir(skills_dir, dry_run)
    count = 0
    for entry in entries:
        # entry looks like "./skills/engineering/tdd"
        skill_name = Path(entry).name
        link = skills_dir / skill_name
        # entry minus "./" prefix → "skills/engineering/tdd"
        sub_path = entry[2:] if entry.startswith("./") else entry
        target = Path(f"../vendor/mattpocock-skills/{sub_path}")
        if dry_run:
            log(f"[DRY-RUN] symlink skills/{skill_name}")
            count += 1
            continue
        # Recreate if missing or pointing at the wrong target
        current = link.readlink() if link.is_symlink() else None
        if current == target:
            count += 1
            continue
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(target)
        count += 1
    if not dry_run:
        log(f"skills/ mattpocock symlinks ({count}, generated from upstream plugin.json)")


def _deep_copy_skills(
    skills_src: Path, skills_out: Path, platform: str, dry_run: bool
) -> None:
    """Copy resolved skill directories (follows symlinks) for git-cloned distribution."""
    ensure_dir(skills_out, dry_run)
    count = 0
    for skill_dir in sorted(skills_src.iterdir()):
        resolved = skill_dir.resolve()
        if not resolved.is_dir():
            continue
        if not _asset_applies_to(skill_dir, platform):
            continue
        dst = skills_out / skill_dir.name
        if dry_run:
            log(f"[DRY-RUN] copy {skill_dir.name}")
        else:
            shutil.copytree(resolved, dst)
            count += 1
    if not dry_run:
        log(f"_dist/{platform}/skills ({count} skills, deep copy)")


def build_dist(dry_run: bool = False) -> None:
    """Generate platform-filtered content in _dist/."""
    log_section("Building _dist/ (platform-filtered content)")

    _ensure_submodules(dry_run)
    _ensure_mattpocock_skill_symlinks(dry_run)

    if not dry_run:
        if DIST.exists():
            shutil.rmtree(DIST)
        DIST.mkdir()

    for platform in ("cursor", "claude", "codex"):
        platform_dir = DIST / platform
        ensure_dir(platform_dir, dry_run)

        # Skills: Codex and Cursor use deep copy (Codex: git clone doesn't init
        # submodules; Cursor: read build artifacts so manifest can point at
        # _dist/cursor/skills/ instead of runtime symlinks into the repo root).
        # Claude uses symlinks, but mattpocock-vendored skills are excluded
        # from the Claude distribution because the mattpocock-skills@mattpocock
        # native plugin provides them.
        skills_src = REPO_ROOT / "skills"
        skills_out = platform_dir / "skills"
        use_deep_copy = platform in ("codex", "cursor")

        if use_deep_copy:
            _deep_copy_skills(skills_src, skills_out, platform, dry_run)
        elif _has_platform_filtered_content(skills_src, platform):
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
                            log(f"[DRY-RUN] copy {agent_file.name}")
                        elif platform == "cursor":
                            # Cursor rejects plugins whose source paths
                            # contain ".." (treats them as "unresolved or
                            # unsafe source path" → "Error loading plugin").
                            # Deep-copy instead of symlinking so no component
                            # path escapes the plugin dir on resolve.
                            shutil.copy2(agent_file, dst)
                        else:
                            dst.symlink_to(Path(f"../../../agents/{agent_file.name}"))
                    if not dry_run:
                        log(f"_dist/{platform}/agents (filtered)")
                else:
                    if dry_run:
                        log(f"[DRY-RUN] {agents_out}")
                    elif platform == "cursor":
                        shutil.copytree(agents_src, agents_out)
                        log(f"_dist/{platform}/agents (deep copy)")
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
                # Codex AGENTS.md = global instructions + common rules only.
                # Language-specific rules (java/python/react) are excluded to
                # stay within Codex's 32KB default limit; those are available
                # via Skills on demand.
                codex_content = gi_content
                common_rules_dir = REPO_ROOT / "rules" / "common"
                rule_sections = []
                if common_rules_dir.exists():
                    for rf in sorted(common_rules_dir.rglob("*.md")):
                        if rule_applies_to(rf, "codex"):
                            rule_sections.append(strip_frontmatter(rf.read_text(encoding="utf-8")))
                if rule_sections:
                    codex_content += "\n\n# --- Rules ---\n\n" + "\n\n".join(rule_sections)
                dst = platform_dir / "AGENTS.md"
                if dry_run:
                    log(f"[DRY-RUN] write {dst}")
                else:
                    dst.write_text(codex_content, encoding="utf-8")
                    size_kb = len(codex_content.encode("utf-8")) / 1024
                    if size_kb > 32:
                        log(f"⚠️  WARNING: Codex AGENTS.md is {size_kb:.1f}KB (exceeds 32KB default limit)")
                        log("  Consider raising project_doc_max_bytes in ~/.codex/config.toml")
                    else:
                        log(f"Codex AGENTS.md: {size_kb:.1f}KB / 32KB")

        if has_rules and not dry_run:
            log(f"_dist/{platform}/rules/ generated")


# ─── Phase 2: Deploy ───────────────────────────────────────────────────────────

THIRD_PARTY_JSON = REPO_ROOT / "third-party.json"


def _load_third_party_plugins() -> list[dict]:
    """Load third-party plugin config from third-party.json."""
    if not THIRD_PARTY_JSON.exists():
        return []
    data = json.loads(THIRD_PARTY_JSON.read_text(encoding="utf-8"))
    return data.get("plugins", [])


def _claude_plugins_to_install() -> list[dict]:
    """Filter third-party plugins that are auto-installable on Claude Code.

    A plugin is auto-installable when its claude platform entry has both
    `marketplace_ref` and `plugin_id`. Entries without these (e.g.
    understand-anything's "Managed via ~/.agents/skills/...") are skipped —
    they are managed manually and logged, not auto-installed.
    """
    result = []
    for plugin in _load_third_party_plugins():
        claude_cfg = plugin.get("platforms", {}).get("claude", {})
        ref = claude_cfg.get("marketplace_ref")
        pid = claude_cfg.get("plugin_id")
        if ref and pid:
            result.append({"name": plugin.get("name", pid), "marketplace_ref": ref, "plugin_id": pid})
    return result


def _ensure_claude_plugin(installed: str, marketplace_ref: str, plugin_id: str) -> None:
    """Install a Claude Code plugin from a marketplace if absent, else update it.

    Both paths check the subprocess return code — a silent `update` that logs
    "updated" on failure is the failure mode this guards against. The
    `marketplace add` return code is intentionally not checked: install is the
    real gate (a failed add surfaces as a failed install right after).
    """
    if plugin_id not in installed:
        subprocess.run(
            ["claude", "plugin", "marketplace", "add", marketplace_ref],
            capture_output=True, text=True,
        )
        result = subprocess.run(
            ["claude", "plugin", "install", plugin_id, "--scope", "user"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            log(f"{plugin_id} installed")
        else:
            log(f"{plugin_id} install failed: {result.stderr.strip()}")
            log(f"Try manually: claude plugin marketplace add {marketplace_ref}")
            log(f"             claude plugin install {plugin_id}")
    else:
        result = subprocess.run(
            ["claude", "plugin", "update", plugin_id],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            log(f"{plugin_id} updated")
        else:
            log(f"{plugin_id} update failed: {result.stderr.strip()}")


def install_claude(dry_run: bool = False) -> None:
    log_section("Deploying Claude Code")

    # 1. Plugins: install those declared in third-party.json (claude platform
    # entries with marketplace_ref + plugin_id). `claude plugin install` does a
    # full clone from GitHub, so skills/, agents/, .mcp.json all work.
    plugins = _claude_plugins_to_install()
    if dry_run:
        for p in plugins:
            log(f"[DRY-RUN] claude plugin install {p['plugin_id']}")
    else:
        # One list call covers all plugins in the config
        list_result = subprocess.run(
            ["claude", "plugin", "list"],
            capture_output=True, text=True,
        )
        installed = list_result.stdout
        for p in plugins:
            _ensure_claude_plugin(installed, p["marketplace_ref"], p["plugin_id"])

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

    # 3. Rules: only deploy common/ rules to user-level ~/.claude/rules/
    rules_common_src = DIST / "claude" / "rules" / "common"
    dst_rules = CLAUDE_HOME / "rules" / "common"
    if rules_common_src.exists():
        if dst_rules.exists() and not dry_run:
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
            log("Language rules available via Skills or project-level .claude/rules/")


def install_codex(dry_run: bool = False) -> None:
    log_section("Deploying Codex")

    # 1. Plugin symlink
    plugin_dir = CODEX_HOME / "plugins" / "local" / "earthchen-ai-assets"
    create_symlink(REPO_ROOT, plugin_dir, dry_run)

    # Register in config.toml (marketplace + enabled plugin)
    config_path = CODEX_HOME / "config.toml"
    if not dry_run and config_path.exists():
        config_text = config_path.read_text(encoding="utf-8")
        if "earthchen-ai-assets" not in config_text:
            additions = (
                '\n[marketplaces.earthchen-ai-assets]\n'
                'last_updated = "2026-07-10T04:21:00Z"\n'
                'source_type = "local"\n'
                f'source = "{REPO_ROOT}"\n'
                '\n[plugins."earthchen-ai-assets@earthchen-ai-assets"]\n'
                'enabled = true\n'
            )
            config_path.write_text(config_text + additions, encoding="utf-8")
            log("Registered plugin in config.toml")

    log("Plugin provides: skills, MCP")

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


def install_cursor(dry_run: bool = False) -> None:
    log_section("Deploying Cursor")

    # Cursor's plugin registry only recognizes plugins installed via the
    # marketplace (each gets a numeric id recorded in state.vscdb's
    # `cursor.plugins.installedIds.<team>|<workspace>` keys). A local symlink
    # under ~/.cursor/plugins/local/ is *not* registered as an installed plugin
    # — it's a dev-preview path that requires a manual Reload Window and is
    # never counted in installedIds, so it silently failed to surface the
    # plugin (e.g. opening this repo's own workspace showed installedIds `[]`).
    #
    # Therefore Cursor, like Claude Code, is deployed via the marketplace:
    #   Settings → Customize → add marketplace URL → install.
    # The committed `_dist/cursor/` is what the marketplace clone loads.
    local_symlink = CURSOR_HOME / "plugins" / "local" / "earthchen-ai-assets"
    if local_symlink.is_symlink() and not dry_run:
        local_symlink.unlink()
        log(f"Removed stale local symlink {local_symlink} (Cursor ignores it)")
    elif local_symlink.is_symlink() and dry_run:
        log(f"[DRY-RUN] remove stale local symlink {local_symlink}")

    log("Plugin provides: rules, skills, agents, MCP (all via native plugin system)")
    log("Install via marketplace: Cursor → Settings → Customize → add URL")
    log("  https://github.com/EarthChen/ai-assets")
    log("Dev preview (optional): symlink this repo to ~/.cursor/plugins/local/ + Reload Window")
    log("  (not counted in installedIds; marketplace install is the source of truth)")


# ─── Version Management ───────────────────────────────────────────────────────

PLUGIN_JSONS = [
    REPO_ROOT / ".cursor-plugin" / "plugin.json",
    REPO_ROOT / ".claude-plugin" / "plugin.json",
    REPO_ROOT / ".codex-plugin" / "plugin.json",
]

MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"


def _get_current_version() -> str:
    """Read version from the first available plugin.json."""
    for pj in PLUGIN_JSONS:
        if pj.exists():
            data = json.loads(pj.read_text(encoding="utf-8"))
            return data.get("version", "0.0.0")
    return "0.0.0"


def _bump_version(current: str, part: str) -> str:
    """Bump major/minor/patch of a semver string."""
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
    for pj in PLUGIN_JSONS:
        if not pj.exists():
            continue
        data = json.loads(pj.read_text(encoding="utf-8"))
        old_ver = data.get("version", "unknown")
        data["version"] = version
        if dry_run:
            log(f"[DRY-RUN] {pj.relative_to(REPO_ROOT)}: {old_ver} -> {version}")
        else:
            pj.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            log(f"{pj.relative_to(REPO_ROOT)}: {old_ver} -> {version}")

    # Update marketplace.json version (critical for Claude Code auto-update)
    if MARKETPLACE_JSON.exists():
        data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
        for plugin in data.get("plugins", []):
            if plugin.get("name") == "earthchen-ai-assets":
                old_ver = plugin.get("version", "unknown")
                plugin["version"] = version
                if dry_run:
                    log(f"[DRY-RUN] marketplace.json: {old_ver} -> {version}")
                else:
                    log(f"marketplace.json: {old_ver} -> {version}")
                break
        if not dry_run:
            MARKETPLACE_JSON.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )

def _deploy_shared_skills(dry_run: bool = False) -> None:
    """Deploy skills to ~/.agents/skills/ via symlinks.

    Legacy fallback for platforms whose plugin system does not support
    skills distribution. Currently unused since all platforms (Cursor,
    Claude Code, Codex) handle skills via their native plugin system.
    """
    skills_dir = REPO_ROOT / "skills"
    dst_skills = AGENTS_HOME / "skills"
    ensure_dir(dst_skills, dry_run)

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        dst = dst_skills / skill_dir.name
        create_symlink(skill_dir.resolve(), dst, dry_run)


# ─── Main ──────────────────────────────────────────────────────────────────────

def _do_install(platform: str, dry_run: bool) -> None:
    """Run platform installers."""
    _ensure_submodules(dry_run)
    _ensure_mattpocock_skill_symlinks(dry_run)
    platforms = {
        "claude": install_claude,
        "codex": install_codex,
        "cursor": install_cursor,
    }
    if platform == "all":
        for installer in platforms.values():
            installer(dry_run)
    else:
        platforms[platform](dry_run)


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

    install_parser = sub.add_parser("install", parents=[parent], help="Only install symlinks to platforms")
    install_parser.add_argument(
        "--platform",
        choices=["claude", "codex", "cursor", "all"],
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

    parser.add_argument(
        "--platform",
        choices=["claude", "codex", "cursor", "all"],
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
    else:
        build_dist(args.dry_run)
        _do_install(args.platform, args.dry_run)

    log_section("Done")
    if not args.dry_run:
        print("\nNext steps:")
        print("  1. Restart agents to pick up changes")
        print("  2. (Optional) Uninstall superpowers plugin if previously installed")
    else:
        print("\nRe-run without --dry-run to apply.")


if __name__ == "__main__":
    main()
