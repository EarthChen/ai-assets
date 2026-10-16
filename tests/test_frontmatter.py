"""Frontmatter parsing and per-platform rule conversion.

Rules are written once in a platform-agnostic form; build translates them
into Claude `.md` (paths CSV) and Cursor `.mdc` (globs JSON). A parsing
regression silently changes which rules load where, so these tests pin the
translation contract.
"""

from __future__ import annotations

from pathlib import Path

from installer import frontmatter


def test_parse_frontmatter_reads_scalars_bools_and_both_list_forms():
    content = (
        "---\n"
        'description: "Java rules"\n'
        "alwaysApply: false\n"
        'globs: ["**/*.ts", "**/*.tsx"]\n'
        "paths:\n"
        '  - "**/*.java"\n'
        "  - '**/*.kt'\n"
        "---\n"
        "\n"
        "# Body\n"
    )
    meta, body = frontmatter.parse_frontmatter(content)
    assert meta == {
        "description": "Java rules",
        "alwaysApply": False,
        "globs": ["**/*.ts", "**/*.tsx"],
        "paths": ["**/*.java", "**/*.kt"],
    }
    assert body == "# Body\n"


def test_parse_frontmatter_without_frontmatter_returns_content_unchanged():
    assert frontmatter.parse_frontmatter("# Title\n") == ({}, "# Title\n")
    # An unterminated block is not frontmatter: the rule must not lose its body.
    assert frontmatter.parse_frontmatter("---\nkey: v\n") == ({}, "---\nkey: v\n")


def test_strip_frontmatter_keeps_only_body():
    assert frontmatter.strip_frontmatter("---\na: b\n---\nbody\n") == "body\n"


def test_convert_rule_to_mdc_without_frontmatter_always_applies(tmp_path: Path):
    rule = tmp_path / "style.md"
    rule.write_text("# Style\n", encoding="utf-8")
    assert frontmatter.convert_rule_to_mdc(rule) == (
        '---\ndescription: "style"\nalwaysApply: true\n---\n# Style\n'
    )


def test_convert_rule_to_mdc_translates_paths_to_globs_and_disables_always_apply(tmp_path: Path):
    # Cursor reads `globs`, not `paths`; a rule scoped by globs must not be
    # always-on.
    rule = tmp_path / "py.md"
    rule.write_text('---\ndescription: "Py"\npaths:\n  - "**/*.py"\n---\nbody\n', encoding="utf-8")
    assert frontmatter.convert_rule_to_mdc(rule) == (
        '---\ndescription: "Py"\nglobs: ["**/*.py"]\nalwaysApply: false\n---\nbody\n'
    )


def test_convert_rule_to_mdc_keeps_explicit_always_apply(tmp_path: Path):
    rule = tmp_path / "r.md"
    rule.write_text("---\ndescription: d\nalwaysApply: true\n---\nb\n", encoding="utf-8")
    assert frontmatter.convert_rule_to_mdc(rule) == '---\ndescription: "d"\nalwaysApply: true\n---\nb\n'


def test_rule_applies_to_honors_platforms_list(tmp_path: Path):
    scoped = tmp_path / "scoped.md"
    scoped.write_text("---\nplatforms: [cursor]\n---\nb\n", encoding="utf-8")
    unscoped = tmp_path / "unscoped.md"
    unscoped.write_text("b\n", encoding="utf-8")
    assert frontmatter.rule_applies_to(scoped, "cursor") is True
    assert frontmatter.rule_applies_to(scoped, "claude") is False
    assert frontmatter.rule_applies_to(unscoped, "codex") is True
