#!/usr/bin/env python3
"""Install the canonical No Admin Access skill for Claude Code and/or Codex."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


SKILL_NAME = "no-admin-access"


def destinations(home: Path, target: str) -> list[Path]:
    paths: list[Path] = []
    if target in {"claude", "both"}:
        paths.append(home / ".claude" / "skills" / SKILL_NAME)
    if target in {"codex", "both"}:
        paths.append(home / ".agents" / "skills" / SKILL_NAME)
    return paths


def install(source: Path, destination: Path, force: bool, dry_run: bool) -> None:
    if destination.is_symlink():
        raise RuntimeError(f"refusing to replace symlink: {destination}")
    if destination.exists() and not force:
        raise FileExistsError(f"already exists: {destination} (use --force to replace it)")
    if dry_run:
        print(f"Would install: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    print(f"Installed: {destination}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Override the user home for testing")
    parser.add_argument("--force", action="store_true", help="Replace an existing copy")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(__file__).resolve().parent / "skill"
    if not (source / "SKILL.md").is_file():
        print(f"canonical skill is missing: {source}", file=sys.stderr)
        return 2
    try:
        for destination in destinations(args.home.expanduser().resolve(), args.target):
            install(source, destination, args.force, args.dry_run)
    except (FileExistsError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

