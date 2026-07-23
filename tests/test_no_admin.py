from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skill" / "scripts" / "no_admin.py"
INSTALLER = ROOT / "install.py"
SPEC = importlib.util.spec_from_file_location("no_admin", HELPER)
assert SPEC and SPEC.loader
NO_ADMIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NO_ADMIN)


class CommandCheckTests(unittest.TestCase):
    def check(self, *parts: str):
        return NO_ADMIN.check_command(list(parts))

    def test_local_npm_install_is_safe(self):
        self.assertEqual(self.check("npm", "install", "vite")["status"], "safe")

    def test_global_npm_install_is_blocked(self):
        result = self.check("npm", "install", "--global", "vite")
        self.assertEqual(result["status"], "blocked")
        self.assertIn("global JavaScript", result["blocked_reasons"][0])

    def test_sudo_is_blocked(self):
        self.assertEqual(self.check("sudo", "apt", "install", "git")["status"], "blocked")

    def test_system_package_install_is_blocked_without_sudo(self):
        self.assertEqual(self.check("apt-get", "install", "git")["status"], "blocked")

    def test_system_service_is_blocked(self):
        self.assertEqual(self.check("systemctl", "restart", "nginx")["status"], "blocked")

    def test_docker_is_review(self):
        self.assertEqual(self.check("docker", "build", ".")["status"], "review")

    def test_unscoped_pip_install_is_review(self):
        self.assertEqual(self.check("python", "-m", "pip", "install", "ruff")["status"], "review")

    def test_user_scoped_pip_install_is_safe(self):
        self.assertEqual(self.check("python", "-m", "pip", "install", "--user", "ruff")["status"], "safe")

    def test_machine_registry_edit_is_blocked(self):
        result = self.check("reg.exe", "add", r"HKLM\Software\Example")
        self.assertEqual(result["status"], "blocked")

    def test_powershell_runas_is_blocked(self):
        result = self.check("powershell.exe", "Start-Process", "setup.exe", "-Verb", "RunAs")
        self.assertEqual(result["status"], "blocked")

    def test_windows_protected_path_is_review(self):
        result = self.check("copy", "file.txt", r"C:\Program Files\Example\file.txt")
        self.assertEqual(result["status"], "review")

    def test_windows_executable_path_is_normalized(self):
        result = self.check(r"C:\Windows\System32\runas.exe", "/user:Administrator", "cmd")
        self.assertEqual(result["status"], "blocked")

    def test_empty_command_raises(self):
        with self.assertRaises(ValueError):
            NO_ADMIN.check_command([])


class ProbeTests(unittest.TestCase):
    def test_probe_finds_project_marker(self):
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / "package.json").write_text("{}", encoding="utf-8")
            result = NO_ADMIN.probe(project)
            self.assertEqual(result["schema_version"], 1)
            self.assertTrue(result["project_writable"])
            self.assertTrue(result["project_markers"]["package.json"])


class InstallerTests(unittest.TestCase):
    def run_installer(self, home: Path, *args: str):
        return subprocess.run(
            [sys.executable, str(INSTALLER), "--home", str(home), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_installs_both_targets(self):
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            result = self.run_installer(home, "--target", "both")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((home / ".claude/skills/no-admin-access/SKILL.md").is_file())
            self.assertTrue((home / ".agents/skills/no-admin-access/SKILL.md").is_file())

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            self.assertEqual(self.run_installer(home, "--target", "codex").returncode, 0)
            second = self.run_installer(home, "--target", "codex")
            self.assertEqual(second.returncode, 1)
            self.assertIn("already exists", second.stderr)

    def test_force_replaces_existing_copy(self):
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            destination = home / ".agents/skills/no-admin-access"
            destination.mkdir(parents=True)
            (destination / "stale.txt").write_text("stale", encoding="utf-8")
            result = self.run_installer(home, "--target", "codex", "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((destination / "stale.txt").exists())
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            result = self.run_installer(home, "--target", "both", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((home / ".claude").exists())
            self.assertFalse((home / ".agents").exists())


if __name__ == "__main__":
    unittest.main()

