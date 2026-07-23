---
name: no-admin-access
description: Keep Claude Code or Codex productive on school, work, library, corporate, shared, or otherwise locked-down computers without administrator, root, or sudo access. Use when the user mentions no admin rights, no sudo, permission denied, managed devices, blocked installers, restricted accounts, inability to use Docker or WSL, global package installation failures, or needing project-local and user-space alternatives.
---

# No Admin Access

Work entirely within the user's existing permissions. Prefer project-local, portable, and user-scoped methods. Never bypass device management, security controls, or organizational policy.

## Start the mode

1. Say `No-admin mode active.`
2. Resolve this skill's directory from the loaded `SKILL.md`.
3. Probe the current environment without attempting elevation:

```bash
python3 <skill-dir>/scripts/no_admin.py probe --path <project-root>
```

On Windows, use `py -3` when `python3` is unavailable.

4. Treat the probe as capability discovery, not permission to change system state.
5. Inspect the project for existing local tools, lockfiles, virtual environments, package scripts, and portable binaries before proposing an install.

## Choose a permitted route

Use this order:

1. Reuse a tool already present in the project or on `PATH`.
2. Use the project's package manager and lockfile.
3. Install into a project-local environment or directory.
4. Use a user-scoped install only when it does not modify managed settings or require elevation.
5. Use a portable binary or archive from an official source when policy permits it.
6. If the task truly requires a system change, stop and provide the smallest specific request for the device administrator.

Common project-local patterns:

- Python: create `.venv` inside the project and install into it. Do not alter system Python.
- Node.js: add a local dependency and run it through the package manager. Avoid `npm -g` and machine-wide installers.
- .NET: use a local tool manifest or `--tool-path`.
- Go: set `GOBIN` to a user-owned or project-owned directory for the command.
- Java: prefer an existing wrapper such as `mvnw` or `gradlew`.
- Rust: reuse an existing user-scoped toolchain. Do not assume a system package manager is available.

Do not rewrite the project's dependency strategy merely to avoid admin access. Match its lockfile and documented tooling.

## Check commands before execution

Run the checker before any install, environment setup, service action, registry edit, permission change, or command aimed outside the project:

```bash
python3 <skill-dir>/scripts/no_admin.py check -- <command> [args...]
```

Interpret the result:

- `safe`: no known privileged pattern was found. Normal task safeguards still apply.
- `review`: the command may depend on a system feature or user-level configuration. Inspect its exact effect before running it.
- `blocked`: do not run it in this mode. Choose a local alternative or ask the administrator.

The checker is a guardrail, not a security sandbox. Commands and scripts can hide side effects.

## Hard rules

- Never run or test `sudo`, `doas`, `pkexec`, `runas`, or an elevation prompt.
- Never ask the user to expose an administrator password, token, or recovery key.
- Never disable antivirus, endpoint protection, certificates, proxies, execution policy, firewall rules, browser policy, or device management.
- Never edit protected system paths, machine-wide registry keys, system services, scheduled tasks, boot settings, or other users' files.
- Do not assume Docker, Podman, WSL, Homebrew, package managers, or virtualization can be installed.
- Do not silently edit shell startup files, `PATH`, user registry, or persistent environment settings. Prefer command-scoped environment variables. Ask before a persistent user-level change.
- Do not use a portable copy of a forbidden tool to evade organizational policy.
- Treat `permission denied` as a constraint to diagnose. Do not broaden permissions with recursive `chmod`, ownership changes, ACL changes, or insecure writable directories.
- Do not weaken dependency verification, TLS, signatures, or source checks to make an installation work.
- Preserve the user's existing files and settings. Never delete caches or configurations solely because they are inaccessible.

## Handle a real admin requirement

When no permitted route can satisfy the task, stop before the blocked step and report:

```text
Completed: <work finished without admin access>
Blocked step: <specific system-level action>
Why it needs admin: <plain-language reason>
Best local option: <viable project/user alternative, or none>
Admin request: <smallest exact change the administrator could make>
Resume after: <verification or command to continue>
```

Do not tell the user to request unrestricted administrator access when one package, feature, path, or policy exception would be enough.

## Limits

This mode cannot make a system-level task user-scoped, guarantee that a portable tool is permitted by workplace policy, or override restrictions enforced by the operating system, security software, network, or organization.

