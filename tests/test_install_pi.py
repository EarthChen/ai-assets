"""pi deploy: skills and agents land in pi-only dirs under ~/.pi/agent/.

~/.agents/skills is also scanned by Codex, so self-owned skills linked there
load twice on Codex (plugin + user dir). pi scans ~/.pi/agent/skills, which no
other harness reads. ~/.agents/skills keeps only third-party links (vendor/)
and whatever the user put there by hand.
"""

from __future__ import annotations

import sys

from conftest import link, make_agent, make_skill

from installer import cli, deploy_pi


def _repo_with_pi_sources(repo):
    make_skill(repo / "skills", "alpha")
    make_skill(repo / "skills", "beta")
    make_skill(repo / "pi" / "skills", "pi-only")
    make_agent(repo / "agents", "reviewer")
    make_agent(repo / "pi" / "agents", "Explore")
    (repo / "_dist" / "pi").mkdir(parents=True)
    (repo / "_dist" / "pi" / "AGENTS.md").write_text("agents\n", encoding="utf-8")


def _links(directory):
    return {p.name: p.resolve() for p in directory.iterdir() if p.is_symlink()}


def test_self_owned_and_pi_only_skills_link_into_pi_skills_dir(sandbox):
    repo = sandbox.repo
    _repo_with_pi_sources(repo)

    deploy_pi.install_pi()

    pi_skills = sandbox.home / ".pi" / "agent" / "skills"
    assert _links(pi_skills) == {
        "alpha": (repo / "skills" / "alpha").resolve(),
        "beta": (repo / "skills" / "beta").resolve(),
        "pi-only": (repo / "pi" / "skills" / "pi-only").resolve(),
    }
    assert not (sandbox.home / ".agents" / "skills").exists()
    assert (sandbox.home / ".pi" / "agent" / "AGENTS.md").read_text(encoding="utf-8") == "agents\n"


def test_migration_removes_only_repo_skill_links_from_agents_skills(sandbox):
    repo = sandbox.repo
    _repo_with_pi_sources(repo)
    shared = sandbox.home / ".agents" / "skills"
    link(shared / "alpha", repo / "skills" / "alpha")          # legacy, live
    link(shared / "renamed", repo / "skills" / "renamed")      # legacy, dead
    tdd = make_skill(repo / "vendor" / "mattpocock-skills" / "skills" / "engineering", "tdd")
    link(shared / "tdd", tdd)                                  # third-party
    link(shared / "anysearch", repo / "vendor" / "anysearch-skill")  # third-party, dead
    hand_made = make_skill(shared, "ccbaga-network")           # user's real dir

    deploy_pi._remove_legacy_agents_skill_links()

    assert sorted(p.name for p in shared.iterdir()) == ["anysearch", "ccbaga-network", "tdd"]
    assert (hand_made / "SKILL.md").is_file()


def test_migration_runs_on_every_install_even_without_pi(sandbox, empty_path):
    # Codex reads ~/.agents/skills, so the legacy links must go even on a
    # machine where pi is no longer detected.
    repo = sandbox.repo
    make_skill(repo / "skills", "alpha")
    placeholder = repo / "vendor" / "mattpocock-skills"
    placeholder.mkdir(parents=True)
    (placeholder / ".placeholder").write_text("", encoding="utf-8")
    shared = sandbox.home / ".agents" / "skills"
    link(shared / "alpha", repo / "skills" / "alpha")

    cli._do_install("all", dry_run=False)

    assert not (shared / "alpha").is_symlink()


def test_migration_dry_run_changes_nothing(sandbox):
    repo = sandbox.repo
    make_skill(repo / "skills", "alpha")
    shared = sandbox.home / ".agents" / "skills"
    link(shared / "alpha", repo / "skills" / "alpha")

    deploy_pi._remove_legacy_agents_skill_links(dry_run=True)

    assert (shared / "alpha").is_symlink()


def test_shared_pi_skills_dir_cleanups_do_not_cross_sources(sandbox):
    # Root skills and pi-only skills share ~/.pi/agent/skills. Each cleanup
    # may only remove dead links into its own source dir.
    repo = sandbox.repo
    _repo_with_pi_sources(repo)
    pi_skills = sandbox.home / ".pi" / "agent" / "skills"
    link(pi_skills / "old-root", repo / "skills" / "old-root")
    link(pi_skills / "old-pi", repo / "pi" / "skills" / "old-pi")

    deploy_pi._clean_stale_skill_symlinks(pi_skills, repo / "skills")
    assert sorted(p.name for p in pi_skills.iterdir()) == ["old-pi"]

    link(pi_skills / "old-root", repo / "skills" / "old-root")
    deploy_pi._clean_stale_skill_symlinks(pi_skills, repo / "pi" / "skills")
    assert sorted(p.name for p in pi_skills.iterdir()) == ["old-root"]


def test_install_pi_removes_stale_links_from_both_skill_sources(sandbox):
    repo = sandbox.repo
    _repo_with_pi_sources(repo)
    pi_skills = sandbox.home / ".pi" / "agent" / "skills"
    link(pi_skills / "old-root", repo / "skills" / "old-root")
    link(pi_skills / "old-pi", repo / "pi" / "skills" / "old-pi")

    deploy_pi.install_pi()

    assert sorted(_links(pi_skills)) == ["alpha", "beta", "pi-only"]


def test_install_pi_removes_stale_pi_only_agent_links_and_keeps_root_agents(sandbox):
    repo = sandbox.repo
    _repo_with_pi_sources(repo)
    pi_agents = sandbox.home / ".pi" / "agent" / "agents"
    link(pi_agents / "OldExplore.md", repo / "pi" / "agents" / "OldExplore.md")
    link(pi_agents / "foreign.md", sandbox.home / "elsewhere.md")

    deploy_pi.install_pi()

    assert sorted(p.name for p in pi_agents.iterdir()) == ["Explore.md", "foreign.md", "reviewer.md"]


def test_single_platform_install_keeps_legacy_links_while_pi_is_detected(
        sandbox, empty_path, monkeypatch):
    # The legacy links are pi's only skill source until install_pi relinks
    # into ~/.pi/agent/skills; a claude-only run must not strip them.
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(cli, "install_claude", lambda dry_run: None)
    monkeypatch.setattr(cli, "install_manual_skills", lambda name, dry_run: None)
    repo = sandbox.repo
    make_skill(repo / "skills", "alpha")
    vendor = repo / "vendor" / "mattpocock-skills"
    vendor.mkdir(parents=True)
    (vendor / ".placeholder").write_text("", encoding="utf-8")
    (sandbox.home / ".claude").mkdir()
    (sandbox.home / ".pi" / "agent").mkdir(parents=True)
    shared = sandbox.home / ".agents" / "skills"
    link(shared / "alpha", repo / "skills" / "alpha")

    cli._do_install("claude", dry_run=False)

    assert (shared / "alpha").is_symlink()
