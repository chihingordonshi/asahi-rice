"""Test the reboot helper with isolated mocks; never touch boot state or reboot."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ZSH = shutil.which("zsh")
FUNCTIONS = ROOT / ".zsh_functions"


@unittest.skipUnless(ZSH, "zsh is required")
class RebootGentooTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="reboot-gentoo-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.log = self.directory / "calls.jsonl"
        self.env = dict(os.environ, HOME=str(self.directory), PATH=str(self.bin))
        # sudo dispatches only to mocks, using a PATH with no system commands.
        self.mock("sudo", "os.execv(sys.argv[1], sys.argv[1:])\n", dispatch=True)
        self.mock("asahi-bless", "if '--get-boot' in sys.argv: print('Gentoo')\n")
        self.mock("systemctl", "")

    def mock(self, name, body, dispatch=False):
        path = self.bin / name
        path.write_text(
            f"#!{sys.executable}\n"
            "import json, os, shutil, sys\n"
            f"with open({str(self.log)!r}, 'a') as log:\n"
            f"    log.write(json.dumps([{name!r}, *sys.argv[1:]]) + '\\n')\n"
            + ("sys.argv[1] = shutil.which(sys.argv[1])\n" if dispatch else "")
            + body
        )
        path.chmod(0o700)

    def run_helper(self, *args, prelude="", epilogue=""):
        return subprocess.run(
            [ZSH, "-f", "-c",
             'source "$1"; shift; ' + prelude + 'reboot-gentoo "$@"' + epilogue,
             "reboot-gentoo-test", str(FUNCTIONS), *args],
            cwd=self.directory, env=self.env, capture_output=True, text=True, timeout=10,
        )

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_help_and_dry_run_are_side_effect_free(self):
        for args in (("--help",), ("-h",), ("--dry-run",)):
            with self.subTest(args=args):
                result = self.run_helper(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.calls(), [])
        self.assertIn("--next --set-boot Gentoo --yes", result.stdout)
        self.assertIn("must report Gentoo", result.stdout)
        self.assertIn("sudo systemctl reboot", result.stdout)

    def test_invalid_arguments_do_nothing(self):
        for args in (("--yes",), ("",), ("Fedora",), ("--dry-run", "extra")):
            with self.subTest(args=args):
                result = self.run_helper(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Usage: reboot-gentoo", result.stderr)
                self.assertEqual(self.calls(), [])

    def test_missing_dependencies_do_not_change_boot_state(self):
        for name in ("sudo", "asahi-bless", "systemctl"):
            with self.subTest(name=name):
                path = self.bin / name
                hidden = self.directory / name
                path.rename(hidden)
                try:
                    result = self.run_helper()
                finally:
                    hidden.rename(path)
                self.assertEqual(result.returncode, 1)
                self.assertIn(f"{name} is required", result.stderr)
                self.assertEqual(self.calls(), [])

    def test_success_selects_one_shot_verifies_then_reboots(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("permanent default is unchanged", result.stdout)
        self.assertEqual(self.calls(), [
            ["sudo", "asahi-bless", "--next", "--set-boot", "Gentoo", "--yes"],
            ["asahi-bless", "--next", "--set-boot", "Gentoo", "--yes"],
            ["sudo", "asahi-bless", "--next", "--get-boot"],
            ["asahi-bless", "--next", "--get-boot"],
            ["sudo", "systemctl", "reboot"],
            ["systemctl", "reboot"],
        ])

    def test_selection_failure_prevents_query_and_reboot(self):
        self.mock("asahi-bless", "sys.exit(7)\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(self.calls()), 2)
        self.assertNotIn("Rebooting into Gentoo", result.stdout)

    def test_query_failure_or_wrong_target_prevents_reboot(self):
        for query in ("sys.exit(8)", "print('Fedora')", "print('')"):
            with self.subTest(query=query):
                self.log.unlink(missing_ok=True)
                self.mock("asahi-bless", f"if '--get-boot' in sys.argv: {query}\n")
                result = self.run_helper()
                self.assertEqual(result.returncode, 1)
                self.assertEqual(len(self.calls()), 4)
                self.assertNotIn("Rebooting into Gentoo", result.stdout)

    def test_reboot_failure_reports_pending_selection_and_cancel_command(self):
        self.mock("systemctl", "sys.exit(9)\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Gentoo remains selected", result.stderr)
        self.assertIn("sudo asahi-bless --clear-next", result.stderr)

    def test_shell_options_are_preserved(self):
        result = self.run_helper(
            "--dry-run", prelude="setopt shwordsplit; ",
            epilogue="; [[ -o shwordsplit ]]",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
