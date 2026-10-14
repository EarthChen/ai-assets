"""pi deploy: AGENTS.md, skill links and agent links.

Self-owned skills link into ~/.agents/skills, the Agent Skills standard dir
that pi and other compliant harnesses scan. pi-only skills link into
~/.pi/agent/skills, which only pi reads. ~/.agents/skills also holds
third-party links (vendor/) and whatever the user put there by hand.
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


def test_self_owned_skills_link_into_agents_skills_and_pi_only_into_pi_dir(sandbox):
    repo = sandbox.repo
    _repo_with_pi_sources(repo)

    deploy_pi.install_pi()

    assert _links(sandbox.home / ".agents" / "skills") == {
        "alpha": (repo / "skills" / "alpha").resolve(),
        "beta": (repo / "skills" / "beta").resolve(),
    }
    assert _links(sandbox.home / ".pi" / "agent" / "skills") == {
        "pi-only": (repo / "pi" / "skills" / "pi-only").resolve(),
    }
    assert (sandbox.home / ".pi" / "agent" / "AGENTS.md").read_text(encoding="utf-8") == "agents\n"


def test_install_pi_removes_self_owned_links_from_pi_skills_dir(sandbox):
    # A self-owned skill linked in both dirs would load twice on pi.
    repo = sandbox.repo
    _repo_with_pi_sources(repo)
    pi_skills = sandbox.home / ".pi" / "agent" / "skills"
    link(pi_skills / "alpha", repo / "skills" / "alpha")

    deploy_pi.install_pi()

    assert sorted(_links(pi_skills)) == ["pi-only"]


def test_agents_skills_cleanup_keeps_third_party_links_and_real_dirs(sandbox):
    repo = sandbox.repo
    _repo_with_pi_sources(repo)
    shared = sandbox.home / ".agents" / "skills"
    link(shared / "renamed", repo / "skills" / "renamed")      # stale self-owned
    tdd = make_skill(repo / "vendor" / "mattpocock-skills" / "skills" / "engineering", "tdd")
    link(shared / "tdd", tdd)                                  # third-party
    link(shared / "anysearch", repo / "vendor" / "anysearch-skill")  # third-party, dead
    hand_made = make_skill(shared, "ccbaga-network")           # user's real dir

    deploy_pi.install_pi()

    assert sorted(p.name for p in shared.iterdir()) == [
        "alpha", "anysearch", "beta", "ccbaga-network", "tdd"]
    assert (hand_made / "SKILL.md").is_file()


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
    shared = sandbox.home / ".agents" / "skills"
    pi_skills = sandbox.home / ".pi" / "agent" / "skills"
    link(shared / "old-root", repo / "skills" / "old-root")
    link(pi_skills / "old-pi", repo / "pi" / "skills" / "old-pi")

    deploy_pi.install_pi()

    assert sorted(_links(shared)) == ["alpha", "beta"]
    assert sorted(_links(pi_skills)) == ["pi-only"]


def test_install_pi_removes_stale_pi_only_agent_links_and_keeps_root_agents(sandbox):
    repo = sandbox.repo
    _repo_with_pi_sources(repo)
    pi_agents = sandbox.home / ".pi" / "agent" / "agents"
    link(pi_agents / "OldExplore.md", repo / "pi" / "agents" / "OldExplore.md")
    link(pi_agents / "foreign.md", sandbox.home / "elsewhere.md")

    deploy_pi.install_pi()

    assert sorted(p.name for p in pi_agents.iterdir()) == ["Explore.md", "foreign.md", "reviewer.md"]


def test_install_without_pi_keeps_self_owned_links(sandbox, empty_path, monkeypatch):
    # The ~/.agents/skills links are pi's skill source; a claude-only run
    # must not strip them.
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(cli, "install_claude", lambda dry_run: None)
    monkeypatch.setattr(cli, "install_manual_skills", lambda name, dry_run: None)
    repo = sandbox.repo
    make_skill(repo / "skills", "alpha")
    vendor = repo / "vendor" / "mattpocock-skills"
    vendor.mkdir(parents=True)
    (vendor / ".placeholder").write_text("", encoding="utf-8")
    (sandbox.home / ".claude").mkdir()
    shared = sandbox.home / ".agents" / "skills"
    link(shared / "alpha", repo / "skills" / "alpha")

    cli._do_install("claude", dry_run=False)

    assert (shared / "alpha").is_symlink()
