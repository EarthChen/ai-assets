"""Symlink primitives and the Cursor real-dir copy filter."""

from __future__ import annotations

from conftest import link, make_skill

from installer import common, deploy_cursor, deploy_pi


def test_create_symlink_never_deletes_a_real_directory(sandbox, capsys):
    # A real directory at the link path is user data (e.g. a hand-installed
    # skill in ~/.agents/skills). Replacing it with a link would destroy it.
    src = make_skill(sandbox.repo / "skills", "alpha")
    dst = sandbox.home / ".pi" / "agent" / "skills" / "alpha"
    dst.mkdir(parents=True)
    (dst / "keep.txt").write_text("user data", encoding="utf-8")

    common.create_symlink(src, dst)

    assert not dst.is_symlink()
    assert (dst / "keep.txt").read_text(encoding="utf-8") == "user data"
    assert "real directory" in capsys.readouterr().out


def test_create_symlink_dry_run_reports_real_directory_skip(sandbox, capsys):
    src = make_skill(sandbox.repo / "skills", "alpha")
    dst = sandbox.home / "skills" / "alpha"
    dst.mkdir(parents=True)

    common.create_symlink(src, dst, dry_run=True)

    out = capsys.readouterr().out
    assert "real directory" in out
    assert "[DRY-RUN] symlink" not in out
    assert dst.is_dir() and not dst.is_symlink()


def test_create_symlink_replaces_an_existing_link(sandbox):
    old = make_skill(sandbox.repo / "skills", "old")
    new = make_skill(sandbox.repo / "skills", "new")
    dst = link(sandbox.home / "skills" / "x", old)

    common.create_symlink(new, dst)

    assert dst.is_symlink() and dst.resolve() == new.resolve()


def test_stale_skill_cleanup_removes_only_dead_links_into_its_source(sandbox):
    src_root = sandbox.repo / "skills"
    live = make_skill(src_root, "live")
    link_dir = sandbox.home / "links"
    link(link_dir / "live", live)
    link(link_dir / "gone", src_root / "gone")
    link(link_dir / "vendor-gone", sandbox.repo / "vendor" / "x" / "gone")

    deploy_pi._clean_stale_skill_symlinks(link_dir, src_root)

    assert sorted(p.name for p in link_dir.iterdir()) == ["live", "vendor-gone"]


def test_stale_agent_cleanup_removes_only_dead_links_into_its_source(sandbox):
    src_root = sandbox.repo / "agents"
    src_root.mkdir()
    (src_root / "live.md").write_text("x", encoding="utf-8")
    link_dir = sandbox.home / "agents"
    link(link_dir / "live.md", src_root / "live.md")
    link(link_dir / "gone.md", src_root / "gone.md")
    link(link_dir / "other.md", sandbox.repo / "pi" / "agents" / "gone.md")

    deploy_pi._clean_stale_agent_symlinks(link_dir, src_root)

    assert sorted(p.name for p in link_dir.iterdir()) == ["live.md", "other.md"]


def test_cursor_copy_skips_local_state_and_tool_caches(sandbox):
    # The Cursor plugin is a real-dir copy of the repo root. Local session
    # state (.claude/settings.local.json, plans), notes and tool caches must
    # not leak into ~/.cursor/plugins/local/.
    repo = sandbox.repo
    make_skill(repo / "skills", "alpha")
    (repo / "skills" / "alpha" / "notes").mkdir()  # skill content, not repo notes
    for name in (".claude", ".agents", "notes", "node_modules", ".venv",
                 ".ruff_cache", ".pytest_cache", "vendor", ".git", "__pycache__"):
        (repo / name).mkdir()
        (repo / name / "f").write_text("x", encoding="utf-8")
    (repo / "skills" / "alpha" / "node_modules").mkdir()

    dst = sandbox.home / ".cursor" / "plugins" / "local" / "p"
    deploy_cursor.copy_plugin_tree(repo, dst)

    assert sorted(p.name for p in dst.iterdir()) == ["skills"]
    assert sorted(p.name for p in (dst / "skills" / "alpha").iterdir()) == ["SKILL.md", "notes"]


def test_cursor_copy_rebuilds_destination(sandbox):
    make_skill(sandbox.repo / "skills", "alpha")
    dst = sandbox.home / "plugin"
    (dst / "stale").mkdir(parents=True)

    deploy_cursor.copy_plugin_tree(sandbox.repo, dst)

    assert not (dst / "stale").exists()
