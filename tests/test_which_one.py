"""Exercise which-one with isolated PATHs and read-only package-manager mocks."""

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
class WhichOneTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="which-one test-", dir=artifacts)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        (self.bin / "python3").symlink_to(sys.executable)
        self.home = self.directory / "home"
        self.home.mkdir()
        self.log = self.directory / "calls.jsonl"
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin))

    def executable(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"#!{sys.executable}\nfrom pathlib import Path\n"
            f"Path({str(self.directory / 'target-was-executed')!r}).touch()\n"
            "raise SystemExit(99)\n"
        )
        path.chmod(0o700)
        return path

    def manager(self, name, responses):
        """Responses are (exact argument list, stdout, exit status) tuples."""
        script = self.bin / name
        script.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            f"with open({str(self.log)!r}, 'a') as log:\n"
            f"    log.write(json.dumps([{name!r}, *sys.argv[1:]]) + '\\n')\n"
            "assert os.environ['LC_ALL'] == 'C'\n"
            "assert os.environ['HOMEBREW_NO_AUTO_UPDATE'] == '1'\n"
            "assert os.environ['HOMEBREW_NO_ANALYTICS'] == '1'\n"
            f"for args, output, code in {responses!r}:\n"
            "    if sys.argv[1:] == args:\n"
            "        sys.stdout.write(output)\n"
            "        sys.exit(code)\n"
            f"if {name!r} != 'rpm':\n"
            "    sys.stderr.write('unexpected mock query')\n"
            "sys.exit(1)\n"
        )
        script.chmod(0o700)

    def brew(self, formulae="", casks="", cellar=None):
        cellar = cellar or self.directory / "Cellar"
        self.manager("brew", [
            (["--cellar"], str(cellar) + "\n", 0),
            (["--caskroom"], str(self.directory / "Caskroom") + "\n", 0),
            (["list", "--formula", "--versions"], formulae, 0),
            (["list", "--cask", "--versions"], casks, 0),
        ])

    def run_helper(self, *args, prelude="", epilogue=""):
        code = 'source "$1"; shift; ' + prelude + 'which-one "$@"' + epilogue
        return subprocess.run(
            [ZSH, "-f", "-c", code, "which-one-test", str(FUNCTIONS), *args],
            cwd=self.directory, env=self.env, capture_output=True, text=True, timeout=20,
        )

    def output(self, *args, **kwargs):
        result = self.run_helper(*args, **kwargs)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def test_usage_and_help(self):
        for args in ((), ("one", "two"), ("",), ("--refresh",)):
            with self.subTest(args=args):
                result = self.run_helper(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Usage: which-one", result.stderr)
        self.assertIn("Usage: which-one", self.output("--help"))
        self.assertFalse(self.log.exists())

    def test_python_dependency_is_reported(self):
        (self.bin / "python3").unlink()
        result = self.run_helper("impala")
        self.assertEqual(result.returncode, 1)
        self.assertIn("python3 is required", result.stderr)

    def test_absent_managers_and_missing_command(self):
        output = self.output("unknown-tool")
        self.assertIn("No external executable on PATH", output)
        for label in ("DNF/RPM", "Homebrew", "Flatpak", "Nix"):
            self.assertRegex(output, label + ": .*not available")
        self.assertIn("does not prove a manual download", output)

    def test_path_order_deduplication_and_no_target_execution(self):
        first = self.executable(self.bin / "tool")
        second = self.executable(self.directory / "other bin/tool")
        self.env["PATH"] = f"{self.bin}:{second.parent}:{self.bin}"
        output = self.output("tool")
        self.assertIn(f"1. {first}", output)
        self.assertIn(f"2. {second}", output)
        self.assertNotIn("3. ", output)
        self.assertFalse((self.directory / "target-was-executed").exists())

    def test_symlink_and_target_rpm_owners_with_copr_and_failed_dnf(self):
        target = self.executable(self.directory / "system/tool")
        link = self.bin / "tool"
        link.symlink_to(target)
        self.manager("rpm", [
            (["-qf", "--qf", "%{NAME}\n", "--", str(link)], "launcher\n", 0),
            (["-qf", "--qf", "%{NAME}\n", "--", str(target)], "real-tool\n", 0),
        ])
        self.manager("dnf", [
            (["--cacheonly", "info", "--installed", "--", "launcher"],
             "From repository : copr:copr.fedorainfracloud.org:owner:project\n", 0),
            (["--cacheonly", "info", "--installed", "--", "real-tool"], "", 1),
        ])
        output = self.output("tool")
        self.assertIn(f"-> {target}", output)
        self.assertIn("RPM owner: launcher, real-tool", output)
        self.assertIn("DNF/COPR: launcher", output)
        self.assertIn("DNF/RPM: real-tool — repository: unknown (cached DNF query failed)", output)

    def test_rpm_package_name_without_executable_and_dnf4_format(self):
        self.manager("rpm", [
            (["-q", "--qf", "%{NAME}\n", "--", "development-files"], "development-files\n", 0),
        ])
        self.manager("dnf", [
            (["--cacheonly", "info", "--installed", "--", "development-files"],
             "From repo    : updates\n", 0),
        ])
        self.assertIn("development-files — repository: updates", self.output("development-files"))

    def test_brew_attributes_different_binary_name_to_formula(self):
        target = self.executable(self.directory / "Cellar/ripgrep/14.1/bin/rg")
        (self.bin / "rg").symlink_to(target)
        self.brew("ripgrep 14.1\n\nother-rg 1.0\n")
        output = self.output("rg")
        self.assertIn("Homebrew formula: ripgrep 14.1; executable path matches", output)
        self.assertNotIn("Homebrew formula: other-rg", output)

    def test_brew_cask_and_flatpak_can_both_match(self):
        self.brew(casks="localsend 1.0\n")
        self.manager("flatpak", [
            (["list", "--app", "--columns=application,name,origin,installation"],
             "org.localsend.localsend_app\tLocalSend\tflathub\tsystem\n", 0),
        ])
        output = self.output("localsend")
        self.assertIn("Homebrew cask: localsend", output)
        self.assertIn("Flatpak: org.localsend.localsend_app", output)
        self.assertIn("flathub, system; name/ID match", output)

    def test_flatpak_suffix_candidates_keep_installations_and_ambiguity(self):
        self.manager("flatpak", [
            (["list", "--app", "--columns=application,name,origin,installation"],
             "org.one.Editor\tEditor One\tflathub\tuser\n"
             "org.two.Editor\tEditor Two\tprivate\tsystem\n"
             "org.one.Editor\tEditor One\tflathub\tsystem\n", 0),
        ])
        output = self.output("Editor")
        self.assertEqual(output.count("ID-suffix candidate"), 3)
        self.assertIn("flathub, user", output)
        self.assertIn("private, system", output)

    def test_nix_modern_named_elements(self):
        self.manager("nix", [
            (["--extra-experimental-features", "nix-command", "profile", "list", "--json"],
             json.dumps({"elements": {"hello": {
                 "storePaths": ["/nix/store/hash-hello-2.12"],
                 "originalUrl": "flake:nixpkgs", "attrPath": "legacyPackages.aarch64-linux.hello",
             }}}), 0),
        ])
        output = self.output("hello")
        self.assertIn("Nix default profile: hello: /nix/store/hash-hello-2.12", output)
        self.assertIn("flake:nixpkgs#legacyPackages.aarch64-linux.hello", output)

    def test_nix_older_json_elements_and_versioned_store_name(self):
        self.manager("nix", [
            (["--extra-experimental-features", "nix-command", "profile", "list", "--json"],
             json.dumps({"elements": [{"storePaths": ["/nix/store/hash-hello-2.12"]}]}), 0),
        ])
        self.assertIn("Nix default profile: 0:", self.output("hello"))

    def test_nix_legacy_fallback_with_multiple_named_outputs(self):
        self.manager("nix", [
            (["--extra-experimental-features", "nix-command", "profile", "list", "--json"],
             "not valid JSON", 0),
        ])
        self.manager("nix-env", [
            (["-q", "--out-path"],
             "hello-2.12  man=/nix/store/hash-hello-2.12-man;/nix/store/other-hello-2.12\n", 0),
        ])
        self.assertIn("Nix default profile: hello-2.12", self.output("hello"))

    def test_query_failures_are_not_reported_as_absence(self):
        rpm = self.bin / "rpm"
        rpm.write_text("#!/nonexistent/which-one-test-interpreter\n")
        rpm.chmod(0o700)
        self.manager("flatpak", [])
        self.manager("nix", [])
        output = self.output("hello")
        self.assertIn("DNF/RPM: query failed", output)
        self.assertNotIn("DNF/RPM: no match", output)
        self.assertIn("Flatpak: query failed", output)
        self.assertNotIn("Flatpak: no match", output)
        self.assertIn("Nix default profile: query failed", output)

    def test_language_package_managers_are_not_checked(self):
        for name in ("cargo", "npm", "pip", "uv"):
            self.manager(name, [])
        output = self.output("impala")
        self.assertFalse(self.log.exists())
        self.assertNotIn("Cargo:", output)

    def test_names_are_not_regular_expressions_or_substring_matches(self):
        self.brew("foo-tool 1.0\n")
        self.manager("flatpak", [
            (["list", "--app", "--columns=application,name,origin,installation"],
             "org.example.foobar\tfoobar\tflathub\tuser\n", 0),
        ])
        self.manager("nix-env", [
            (["-q", "--out-path"], "foo-tool-1.0 /nix/store/hash-foo-tool-1.0\n", 0),
        ])
        output = self.output("foo.*")
        self.assertIn("Homebrew: no matching record found", output)
        self.assertIn("Flatpak: no match", output)
        self.assertIn("Nix default profile: no match", output)

    def test_shell_shadowing_and_caller_state_are_preserved(self):
        self.executable(self.bin / "tool")
        output = self.output(
            "tool", prelude='tool() { return 99; }; setopt shwordsplit; wo_before=$PATH; ',
            epilogue='; [[ "$PATH" == "$wo_before" && -o shwordsplit ]]',
        )
        self.assertIn("tool is a shell function", output)
        self.assertIn("1. ", output)


if __name__ == "__main__":
    unittest.main()
