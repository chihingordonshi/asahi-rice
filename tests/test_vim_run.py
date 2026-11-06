"""Exercise :run in isolated Vim sessions without loading installed plugins."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VIM = shutil.which("vim")


def vim_string(value):
    return "'" + str(value).replace("'", "''") + "'"


@unittest.skipUnless(VIM, "Vim is required")
class VimRunTest(unittest.TestCase):
    def setUp(self):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="vim-run-", dir=artifacts)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        runtime = self.directory / "runtime"
        (runtime / "autoload").mkdir(parents=True)
        (runtime / "colors").mkdir()
        (runtime / "autoload/plug.vim").write_text(
            "function! plug#begin(...)\n"
            "  command! -nargs=+ Plug echo ''\n"
            "endfunction\n"
            "function! plug#end(...)\nendfunction\n"
        )
        (runtime / "colors/catppuccin.vim").write_text(
            "let g:colors_name = 'catppuccin'\n"
        )
        self.prelude = (
            "set nomore\nset shell=/bin/sh\n"
            f"execute 'set runtimepath^=' . fnameescape({vim_string(runtime)})\n"
            f"execute 'source ' . fnameescape({vim_string(ROOT / '.vimrc')})\n"
        )

    def run_vim(self, commands, path=None):
        script = self.directory / "test.vim"
        errors = self.directory / "errors"
        script.write_text(
            self.prelude + commands + "\n"
            "if !empty(v:errors)\n"
            f"  call writefile(v:errors, {vim_string(errors)})\n"
            "  cquit\nendif\nqa!\n"
        )
        env = {**os.environ}
        if path is not None:
            env["PATH"] = str(path)
        result = subprocess.run(
            [VIM, "-Nu", "NONE", "-n", "-i", "NONE", "-es", "-S", str(script)],
            cwd=self.directory, env=env, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(
            result.returncode, 0,
            result.stdout + result.stderr + (errors.read_text() if errors.exists() else ""),
        )
        return result.stdout + result.stderr

    @unittest.skipUnless(shutil.which("g++"), "g++ is required")
    def test_lowercase_run_saves_rebuilds_and_quotes_filename(self):
        source = self.directory / "current % # ! ' code.cpp"
        source.write_text('#include <cstdio>\nint main() { puts("OLD_BUILD"); }\n')
        output = self.run_vim(
            f"execute 'edit ' . fnameescape({vim_string(source)})\n"
            "call setline(2, 'int main() { puts(\"FIRST_BUILD\"); }')\n"
            'call feedkeys(":run\\<CR>", \'xt\')\n'
            "call setline(2, 'int main() { puts(\"SECOND_BUILD\"); }')\n"
            "Run\n"
        )
        self.assertIn("FIRST_BUILD", output)
        self.assertIn("SECOND_BUILD", output)
        self.assertNotIn("OLD_BUILD", output)
        self.assertIn("SECOND_BUILD", source.read_text())
        self.assertFalse(source.with_suffix("").exists())

    @unittest.skipUnless(shutil.which("g++"), "g++ is required")
    def test_failed_recompile_does_not_run_previous_build(self):
        source = self.directory / "broken.cpp"
        source.write_text('#include <cstdio>\nint main() { puts("PROGRAM_RAN"); }\n')
        output = self.run_vim(
            f"execute 'edit ' . fnameescape({vim_string(source)})\n"
            "Run\n"
            "call setline(2, 'int main() { syntax error }')\n"
            "Run\n"
        )
        self.assertEqual(output.count("PROGRAM_RAN"), 1)
        self.assertIn("error:", output)
        self.assertIn("syntax error", source.read_text())

    def test_compiler_fallback_and_temporary_binary_cleanup(self):
        for compiler in ("g++", "clang++"):
            with self.subTest(compiler=compiler):
                binaries = self.directory / compiler
                binaries.mkdir()
                log = self.directory / "binary-path"
                mock = binaries / compiler
                mock.write_text(
                    f"#!{sys.executable}\n"
                    "from pathlib import Path\nimport sys\n"
                    "output = Path(sys.argv[sys.argv.index('-o') + 1])\n"
                    f"Path({str(log)!r}).write_text(str(output))\n"
                    "output.write_text('#!/bin/sh\\necho MOCK_PROGRAM_RAN\\n')\n"
                    "output.chmod(0o700)\n"
                )
                mock.chmod(0o700)
                source = self.directory / "mock.cpp"
                source.write_text("int main() {}\n")
                output = self.run_vim(
                    f"execute 'edit ' . fnameescape({vim_string(source)})\n"
                    "Run\n"
                    f"call assert_false(filereadable(readfile({vim_string(log)})[0]))\n",
                    path=binaries,
                )
                self.assertIn("MOCK_PROGRAM_RAN", output)

    def test_rejects_unnamed_non_cpp_and_missing_compiler(self):
        source = self.directory / "test.cpp"
        source.write_text("int main() {}\n")
        empty_path = self.directory / "no-compilers"
        empty_path.mkdir()
        self.run_vim(
            "function! ExpectRunError(message) abort\n"
            "  try\n    Run\n    call assert_report('Run unexpectedly succeeded')\n"
            "  catch\n    call assert_match(a:message, v:exception)\n  endtry\n"
            "endfunction\n"
            "call ExpectRunError('open a C++ file first')\n"
            "new notes.txt\n"
            "call ExpectRunError('current file is not C++')\n"
            f"execute 'edit ' . fnameescape({vim_string(source)})\n"
            "call ExpectRunError('install g++ or clang++ first')\n",
            path=empty_path,
        )


if __name__ == "__main__":
    unittest.main()
