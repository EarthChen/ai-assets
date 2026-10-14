"""Logging and filesystem primitives shared by every installer step."""

from __future__ import annotations

import shutil
from pathlib import Path


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
    if dst.is_dir() and not dst.is_symlink():
        # A real directory at the link path is user data (e.g. a hand-installed
        # skill); never delete it to make room for a link.
        prefix = "[DRY-RUN] " if dry_run else ""
        log(f"{prefix}WARNING: {dst} is a real directory, not a symlink; "
            f"skipped link to {src} (remove it by hand to let install manage it)")
        return
    if dst.is_symlink() or dst.exists():
        if dry_run:
            log(f"[DRY-RUN] relink {dst}")
        else:
            dst.unlink()
    if dry_run:
        log(f"[DRY-RUN] symlink {dst} -> {src}")
    else:
        dst.symlink_to(src)
        log(f"Symlinked {dst.name} -> {src}")
