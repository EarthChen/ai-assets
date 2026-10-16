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
