"""Golden test: the committed `_dist/` equals a fresh build of the repo.

All platforms consume `_dist/` (rules, CLAUDE.md, AGENTS.md, mcp.json). A
mismatch means either the build changed behavior or someone edited a build
input (rules/, global-instructions.md, mcp.json) without running
`uv run install.py build`. Both must fail loudly.

The build runs as a subprocess in a copy of the build inputs, so it never
writes the real `_dist/` and exercises the real `install.py` entrypoint.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
# conftest blocks subprocess.run per test; this module binds the real one at
# import time, before any fixture runs.
_REAL_RUN = subprocess.run

BUILD_INPUT_FILES = ("install.py", "global-instructions.md", "mcp.json")
BUILD_INPUT_DIRS = ("installer", "rules", ".claude-plugin")


def _copy_build_inputs(src: Path, dst: Path) -> None:
    for name in BUILD_INPUT_FILES:
        if (src / name).exists():
            shutil.copy2(src / name, dst / name)
    for name in BUILD_INPUT_DIRS:
        if (src / name).is_dir():
            shutil.copytree(src / name, dst / name,
                            ignore=shutil.ignore_patterns("__pycache__"))
    # A non-empty submodule dir stops build from running `git submodule
    # update` in a directory that is not a git checkout.
    placeholder = dst / "vendor" / "mattpocock-skills"
    placeholder.mkdir(parents=True)
    (placeholder / ".placeholder").write_text("", encoding="utf-8")


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_committed_dist_matches_fresh_build(tmp_path: Path):
    work = tmp_path / "copy"
    work.mkdir()
    _copy_build_inputs(REAL_REPO, work)

    result = _REAL_RUN([sys.executable, "install.py", "build"],
                       cwd=work, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    built = _snapshot(work / "_dist")
    committed = _snapshot(REAL_REPO / "_dist")
    assert built, "build produced no files"
    differing = sorted(
        name for name in built.keys() | committed.keys()
        if built.get(name) != committed.get(name)
    )
    assert not differing, (
        "_dist/ is stale or the build changed; run `uv run install.py build`. "
        f"Differing files: {differing}"
    )
