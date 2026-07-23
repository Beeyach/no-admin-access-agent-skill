# No Admin Access

[![CI](https://github.com/Beeyach/no-admin-access-agent-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/Beeyach/no-admin-access-agent-skill/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An open-source Agent Skill that helps Claude Code and Codex work on locked-down computers without `sudo`, administrator rights, global installs, Docker setup, system services, or machine-wide changes.

No Admin Access is for school laptops, work computers, library machines, managed corporate devices, shared computers, restricted shells, and any development environment where the user cannot elevate privileges.

## What changes

With the skill active, the coding agent:

- Reuses existing project tools before installing anything
- Prefers project-local dependencies, virtual environments, wrappers, and portable tools
- Checks install and setup commands for privileged patterns
- Blocks known elevation and machine-wide changes
- Marks uncertain commands for review instead of guessing
- Never weakens endpoint security or organizational controls
- Stops with one specific administrator request when no user-space route exists

It does not pretend every task can be completed without admin access. It makes the boundary visible before the agent gets stuck halfway through a setup.

## Example

```text
User: Add Prettier, but this is a locked work laptop and I cannot install anything globally.

No-admin mode active.

Existing project: package.json + package-lock.json
Safe route: add Prettier as a local dev dependency
Run: npm install --save-dev prettier
Use: npm exec prettier -- --check .
System changes: none
```

If the agent proposes `npm install -g prettier`, the checker returns:

```text
Result: blocked
Blocked: global JavaScript package installation is outside the project
Option: Add a local dependency and run it through npm exec, npx, pnpm exec, or yarn exec.
```

## Install

Requires Python 3.9 or newer. Installation writes only inside your user folder.

Install for both Claude Code and Codex:

```bash
python install.py --target both
```

Install for one agent:

```bash
python install.py --target claude
python install.py --target codex
```

On Windows, use `py -3` if `python` is unavailable.

The installer copies the canonical skill to:

| Agent | User skill folder |
|---|---|
| Claude Code | `~/.claude/skills/no-admin-access` |
| Codex | `~/.agents/skills/no-admin-access` |

Use `--dry-run` to see the destinations. Use `--force` only when replacing an existing copy of this skill.

## Use

Invoke the skill directly:

```text
$no-admin-access Set up this project without administrator rights.
```

Claude Code can also surface installed skills as slash commands:

```text
/no-admin-access
```

Natural phrases such as these should also trigger it:

- “I do not have sudo on this server.”
- “This is a managed work laptop.”
- “Install it without admin rights.”
- “Docker and WSL are blocked.”
- “Permission denied when the agent tries a global install.”

## Command checker

The bundled helper can inspect a proposed command:

```bash
python skill/scripts/no_admin.py check -- sudo apt install ripgrep
python skill/scripts/no_admin.py check -- npm install -g prettier
python skill/scripts/no_admin.py check -- docker build .
```

Possible results:

| Result | Meaning |
|---|---|
| `safe` | No known privileged pattern was found |
| `review` | The command may rely on a managed feature or persistent setting |
| `blocked` | The command contains a known elevation or machine-wide action |

This is a pattern checker, not a security sandbox. Scripts and package hooks can hide side effects.

## Environment probe

The probe reports writable locations, installed tools, project markers, and whether the current shell is already elevated. It never attempts elevation.

```bash
python skill/scripts/no_admin.py probe --path .
python skill/scripts/no_admin.py probe --path . --json
```

## Supported systems

- Windows
- macOS
- Linux
- Claude Code
- Codex

The helper uses only the Python standard library.

## Safety boundary

No Admin Access will not:

- Ask for or handle an administrator password
- Run privilege escalation tools
- Disable antivirus, endpoint protection, TLS, proxies, firewalls, or device management
- Modify machine-wide registry keys, services, boot settings, or protected system paths
- Use portable software to evade school or workplace policy
- Turn a system-level requirement into a fake user-space solution

See [SECURITY.md](SECURITY.md) for reporting security concerns.

## Contributing

Useful contributions include new command patterns, better user-space alternatives, platform-specific tests, and reproducible restricted-environment failures. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)

