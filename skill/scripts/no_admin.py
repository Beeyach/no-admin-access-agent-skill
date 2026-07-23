#!/usr/bin/env python3
"""Probe a restricted computer and flag commands that may require admin rights."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path, PureWindowsPath
import platform
import re
import shutil
import sys
from typing import Any


PRIVILEGE_TOOLS = {"sudo", "doas", "pkexec", "runas"}
SYSTEM_PACKAGE_MANAGERS = {"apt", "apt-get", "apk", "dnf", "yum", "pacman", "zypper"}
SYSTEM_SERVICE_TOOLS = {"systemctl", "service", "launchctl"}
GLOBAL_FLAGS = {"-g", "--global"}


def _is_elevated() -> bool | None:
    if os.name == "nt":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return None
    if hasattr(os, "geteuid"):
        return os.geteuid() == 0
    return None


def _writable(path: Path) -> bool:
    try:
        return path.exists() and os.access(path, os.W_OK)
    except OSError:
        return False


def probe(path: Path) -> dict[str, Any]:
    project = path.expanduser().resolve()
    home = Path.home().resolve()
    candidates = [
        "python3", "python", "py", "node", "npm", "pnpm", "yarn", "corepack",
        "git", "go", "cargo", "rustup", "java", "mvn", "gradle", "dotnet",
        "docker", "podman", "winget", "brew",
    ]
    tools = {name: shutil.which(name) for name in candidates}
    return {
        "schema_version": 1,
        "platform": platform.system().lower() or "unknown",
        "project": str(project),
        "project_writable": _writable(project),
        "home": str(home),
        "home_writable": _writable(home),
        "elevated": _is_elevated(),
        "available_tools": {key: value for key, value in tools.items() if value},
        "project_markers": {
            marker: (project / marker).exists()
            for marker in (
                ".venv", "package.json", "package-lock.json", "pnpm-lock.yaml",
                "yarn.lock", "uv.lock", "pyproject.toml", "requirements.txt",
                "Cargo.toml", "go.mod", "gradlew", "mvnw", "dotnet-tools.json",
            )
        },
    }


def _command_name(value: str) -> str:
    stripped = value.strip('"\'')
    name = PureWindowsPath(stripped).name if "\\" in stripped else Path(stripped).name
    name = name.lower()
    return name[:-4] if name.endswith(".exe") else name


def _looks_like_system_path(value: str) -> bool:
    normalized = value.strip('"\'').replace("\\", "/").lower()
    prefixes = (
        "/etc/", "/usr/", "/bin/", "/sbin/", "/opt/", "/var/lib/", "/library/",
        "c:/windows/", "c:/program files/", "c:/program files (x86)/", "c:/programdata/",
        "hklm/", "hkey_local_machine/",
    )
    return normalized.startswith(prefixes)


def check_command(command: list[str]) -> dict[str, Any]:
    if not command:
        raise ValueError("a command is required after --")

    executable = _command_name(command[0])
    lowered = [part.lower() for part in command]
    joined = " ".join(lowered)
    blocked: list[str] = []
    review: list[str] = []
    alternatives: list[str] = []

    if executable in PRIVILEGE_TOOLS:
        blocked.append(f"{executable} requests privilege elevation")
        alternatives.append("Use a project-local or user-scoped method, or request the exact admin change.")

    if executable in SYSTEM_PACKAGE_MANAGERS and any(
        action in lowered[1:] for action in ("install", "remove", "upgrade", "update", "add", "del")
    ):
        blocked.append(f"{executable} changes system-managed packages")
        alternatives.append("Use the project's package manager, virtual environment, wrapper, or a policy-approved portable build.")

    if executable in SYSTEM_SERVICE_TOOLS:
        blocked.append(f"{executable} controls system services")
        alternatives.append("Run a user-owned foreground process when the project supports it, or request one specific service change.")

    if executable in {"npm", "pnpm", "yarn"} and any(flag in lowered for flag in GLOBAL_FLAGS):
        blocked.append("global JavaScript package installation is outside the project")
        alternatives.append("Add a local dependency and run it through npm exec, npx, pnpm exec, or yarn exec.")

    if executable in {"pip", "pip3", "python", "python3", "py"} and "install" in lowered:
        if not any(part in lowered for part in ("--user", "--target")):
            review.append("Python installation is not visibly scoped to a virtual environment, --user, or --target")
            alternatives.append("Create or activate a project .venv, then install into it.")

    if executable in {"winget", "msiexec", "choco", "chocolatey"}:
        if executable == "winget" and "--scope" in lowered and "user" in lowered:
            review.append("the installer requests user scope, but the package may still require elevation")
        else:
            blocked.append(f"{executable} may perform a machine-wide Windows installation")
            alternatives.append("Use an official portable archive or a user-scope package if policy permits it.")

    if executable in {"docker", "podman", "wsl"}:
        review.append(f"{executable} depends on a preconfigured runtime or operating-system feature")
        alternatives.append("Use it only if it already works for this account. Do not install or reconfigure it in no-admin mode.")

    if executable in {"chmod", "chown", "icacls", "takeown"}:
        review.append(f"{executable} changes permissions or ownership")
        alternatives.append("Fix the operation's target or choose a user-owned directory instead of broadening permissions.")

    if executable in {"reg", "regedit"} and re.search(r"\b(add|delete|import|restore)\b", joined):
        if "hklm" in joined or "hkey_local_machine" in joined:
            blocked.append("the command changes the machine-wide Windows registry")
        else:
            review.append("the command changes persistent Windows registry state")

    if executable in {"sc", "schtasks", "bcdedit"}:
        blocked.append(f"{executable} changes machine services, scheduled tasks, or boot settings")

    if executable in {"powershell", "pwsh"} and re.search(r"start-process.*-verb\s+runas", joined):
        blocked.append("PowerShell requests an administrator elevation prompt")

    protected_args = [part for part in command[1:] if _looks_like_system_path(part)]
    if protected_args:
        review.append("the command references a protected system path: " + ", ".join(protected_args[:3]))

    if blocked:
        status, exit_code = "blocked", 3
    elif review:
        status, exit_code = "review", 2
    else:
        status, exit_code = "safe", 0

    return {
        "schema_version": 1,
        "status": status,
        "exit_code": exit_code,
        "command": command,
        "blocked_reasons": blocked,
        "review_reasons": review,
        "alternatives": list(dict.fromkeys(alternatives)),
        "warning": "Pattern check only. Scripts and commands may hide privileged side effects.",
    }


def _probe_text(data: dict[str, Any]) -> str:
    elevated = data["elevated"]
    elevation = "unknown" if elevated is None else ("yes" if elevated else "no")
    markers = [name for name, present in data["project_markers"].items() if present]
    return "\n".join([
        f"Platform: {data['platform']}",
        f"Elevated now: {elevation} (no elevation was attempted)",
        f"Project writable: {'yes' if data['project_writable'] else 'no'}",
        f"Home writable: {'yes' if data['home_writable'] else 'no'}",
        f"Project tooling: {', '.join(markers) if markers else 'no common markers found'}",
        f"Available tools: {', '.join(data['available_tools']) if data['available_tools'] else 'none detected'}",
    ])


def _check_text(data: dict[str, Any]) -> str:
    lines = [f"Result: {data['status']}"]
    for reason in data["blocked_reasons"]:
        lines.append(f"Blocked: {reason}")
    for reason in data["review_reasons"]:
        lines.append(f"Review: {reason}")
    for alternative in data["alternatives"]:
        lines.append(f"Option: {alternative}")
    lines.append(data["warning"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="no_admin", description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    probe_parser = sub.add_parser("probe", help="Inspect user-space capabilities without elevation")
    probe_parser.add_argument("--path", type=Path, default=Path.cwd())
    probe_parser.add_argument("--json", action="store_true", dest="as_json")
    check_parser = sub.add_parser("check", help="Flag a command that may require admin rights")
    check_parser.add_argument("--json", action="store_true", dest="as_json")
    check_parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "probe":
        data = probe(args.path)
        print(json.dumps(data, indent=2, sort_keys=True) if args.as_json else _probe_text(data))
        return 0

    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    try:
        data = check_command(command)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 64
    print(json.dumps(data, indent=2, sort_keys=True) if args.as_json else _check_text(data))
    return int(data["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

