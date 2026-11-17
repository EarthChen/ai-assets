"""third-party.json `install` objects -> (link, target) symlink pairs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import make_skill

from installer import third_party


def test_links_form_points_every_link_at_source_root(sandbox):
    source = sandbox.repo / "vendor" / "one"
    pairs = third_party._expand_install_links(
        {"links": ["~/.claude/skills/one", "~/.agents/skills/one"]}, source)
    assert pairs == [
        (sandbox.home / ".claude" / "skills" / "one", source),
        (sandbox.home / ".agents" / "skills" / "one", source),
    ]


def test_generate_from_manifest_field_links_each_listed_skill(sandbox):
    source = sandbox.repo / "vendor" / "multi"
    (source / ".claude-plugin").mkdir(parents=True)
    (source / ".claude-plugin" / "plugin.json").write_text(json.dumps(
        {"skills": ["./skills/eng/tdd", "skills/prod/teach"]}), encoding="utf-8")
    pairs = third_party._expand_install_links({"generate": {
        "from": ".claude-plugin/plugin.json", "field": "skills", "link_dir": "~/.agents/skills",
    }}, source)
    assert pairs == [
        (sandbox.home / ".agents" / "skills" / "tdd", source / "skills/eng/tdd"),
        (sandbox.home / ".agents" / "skills" / "teach", source / "skills/prod/teach"),
    ]


def test_generate_scan_dir_skips_dirs_without_skill_md_and_fans_out_to_extra_links(sandbox):
    source = sandbox.repo / "vendor" / "scan"
    make_skill(source / "skills", "alpha")
    (source / "skills" / "shared").mkdir()  # library code, not a skill
    pairs = third_party._expand_install_links({"generate": {
        "scan_dir": "skills", "link_dir": "~/.agents/skills", "extra_links": ["~/.claude/skills"],
    }}, source)
    target = source / "skills" / "alpha"
    assert pairs == [
        (sandbox.home / ".agents" / "skills" / "alpha", target),
        (sandbox.home / ".claude" / "skills" / "alpha", target),
    ]


@pytest.mark.parametrize("install", [
    {"links": [], "generate": {}},
    {"generate": {"from": "x", "field": "y", "scan_dir": "z", "link_dir": "~"}},
])
def test_ambiguous_install_objects_are_rejected(install):
    with pytest.raises(ValueError):
        third_party._expand_install_links(install, Path("/nonexistent"))


def test_install_object_without_links_or_generate_yields_nothing():
    assert third_party._expand_install_links({"source": "vendor/x"}, Path("/nonexistent")) == []


def test_frontmatter_patch_injects_declared_keys_and_is_idempotent(sandbox):
    vendor = sandbox.repo / "vendor" / "upstream"
    make_skill(vendor / "skills", "alpha")
    (sandbox.repo / "third-party.json").write_text(json.dumps({"plugins": [{
        "name": "upstream", "platforms": {},
        "install": {"source": "vendor/upstream", "frontmatter": {"disable-model-invocation": True},
                    "generate": {"scan_dir": "skills", "link_dir": "~/.agents/skills"}},
    }]}), encoding="utf-8")

    third_party.install_manual_skills(None)

    skill_md = vendor / "skills" / "alpha" / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    assert content.startswith("---\ndisable-model-invocation: true\nname: alpha\n")

    # Rerun (e.g. after a submodule upgrade re-applies nothing): no duplicate line.
    third_party.install_manual_skills(None)
    assert skill_md.read_text(encoding="utf-8") == content


def test_frontmatter_patch_leaves_existing_value_alone(sandbox):
    vendor = sandbox.repo / "vendor" / "upstream"
    skill = make_skill(vendor / "skills", "alpha")
    skill_md = skill / "SKILL.md"
    skill_md.write_text("---\nname: alpha\ndisable-model-invocation: true\n---\nbody",
                        encoding="utf-8")
    (sandbox.repo / "third-party.json").write_text(json.dumps({"plugins": [{
        "name": "upstream", "platforms": {},
        "install": {"source": "vendor/upstream", "frontmatter": {"disable-model-invocation": True},
                    "generate": {"scan_dir": "skills", "link_dir": "~/.agents/skills"}},
    }]}), encoding="utf-8")

    third_party.install_manual_skills(None)

    assert "disable-model-invocation: true\nname: alpha" not in skill_md.read_text(encoding="utf-8")


def test_third_party_link_never_replaces_a_self_owned_skill(sandbox, capsys):
    # install_manual_skills runs after the self-owned links, so a same-name
    # third-party skill would silently take over ~/.agents/skills/<name>.
    own = make_skill(sandbox.repo / "skills", "show-me")
    vendor = sandbox.repo / "vendor" / "upstream"
    make_skill(vendor / "skills", "show-me")
    make_skill(vendor / "skills", "upstream-only")
    (sandbox.repo / "third-party.json").write_text(json.dumps({"plugins": [{
        "name": "upstream", "platforms": {},
        "install": {"source": "vendor/upstream", "generate": {
            "scan_dir": "skills", "link_dir": "~/.agents/skills"}},
    }]}), encoding="utf-8")
    link_dir = sandbox.home / ".agents" / "skills"
    link_dir.mkdir(parents=True)
    (link_dir / "show-me").symlink_to(own)

    third_party.install_manual_skills(None)

    assert (link_dir / "show-me").resolve() == own.resolve()
    assert (link_dir / "upstream-only").resolve() == (vendor / "skills" / "upstream-only").resolve()
    out = capsys.readouterr().out
    assert "ERROR" in out and "show-me" in out
