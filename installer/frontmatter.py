"""Rule frontmatter parsing and per-platform rule conversion."""

from __future__ import annotations

import json
from pathlib import Path


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
