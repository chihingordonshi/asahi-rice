"""Validate keyboard remaps with libxkbcommon, without sending live key events."""

import ctypes
import ctypes.util
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
KEYMAP = ROOT / ".config/hypr/keyboard.xkb"
EFFECTIVE = 1 << 3  # XKB_STATE_MODS_EFFECTIVE
ESCAPE = 0xFF1B


class KeyboardRemapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        library = ctypes.util.find_library("xkbcommon")
        if library is None:
            raise unittest.SkipTest("libxkbcommon is not installed")
        cls.xkb = ctypes.CDLL(library)
        ptr, uint, integer, string = (
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p,
        )
        signatures = {
            "xkb_context_new": ([integer], ptr),
            "xkb_context_unref": ([ptr], None),
            "xkb_keymap_new_from_string": ([ptr, string, integer, integer], ptr),
            "xkb_keymap_unref": ([ptr], None),
            "xkb_keymap_key_by_name": ([ptr, string], uint),
            "xkb_state_new": ([ptr], ptr),
            "xkb_state_unref": ([ptr], None),
            "xkb_state_update_key": ([ptr, uint, integer], integer),
            "xkb_state_key_get_one_sym": ([ptr, uint], uint),
            "xkb_state_serialize_mods": ([ptr, integer], uint),
            "xkb_state_mod_name_is_active": ([ptr, string, integer], integer),
        }
        for name, (args, result) in signatures.items():
            function = getattr(cls.xkb, name)
            function.argtypes, function.restype = args, result
        context = cls.xkb.xkb_context_new(0)
        if not context:
            raise AssertionError("failed to create XKB context")
        cls.addClassCleanup(cls.xkb.xkb_context_unref, context)
        cls.keymap = cls.xkb.xkb_keymap_new_from_string(
            context, KEYMAP.read_bytes(), 1, 0,  # XKB_KEYMAP_FORMAT_TEXT_V1
        )
        if not cls.keymap:
            raise AssertionError("failed to compile keyboard keymap")
        cls.addClassCleanup(cls.xkb.xkb_keymap_unref, cls.keymap)

    def setUp(self):
        self.state = self.xkb.xkb_state_new(self.keymap)
        self.assertTrue(self.state)
        self.addCleanup(self.xkb.xkb_state_unref, self.state)

    def key(self, name):
        code = self.xkb.xkb_keymap_key_by_name(self.keymap, name.encode())
        self.assertNotEqual(code, 0xFFFFFFFF, name)
        return code

    def update(self, name, pressed):
        self.xkb.xkb_state_update_key(self.state, self.key(name), int(pressed))

    def symbol(self, name):
        return self.xkb.xkb_state_key_get_one_sym(self.state, self.key(name))

    def modifiers(self):
        return self.xkb.xkb_state_serialize_mods(self.state, EFFECTIVE)

    def test_right_command_is_escape_without_super_or_other_modifiers(self):
        self.assertEqual(self.symbol("RWIN"), ESCAPE)
        self.update("RWIN", True)
        self.assertEqual(self.symbol("RWIN"), ESCAPE)
        self.assertEqual(self.modifiers(), 0)
        self.assertEqual(self.symbol("AC01"), ord("a"))
        self.update("RWIN", False)
        self.assertEqual(self.modifiers(), 0)

    def test_both_options_remain_alt_not_escape(self):
        for name, symbol in (("LALT", 0xFFE9), ("RALT", 0xFFEA)):
            with self.subTest(key=name):
                self.assertEqual(self.symbol(name), symbol)
                self.update(name, True)
                self.assertEqual(self.symbol(name), symbol)
                self.assertEqual(
                    self.xkb.xkb_state_mod_name_is_active(self.state, b"Mod1", EFFECTIVE), 1,
                )
                self.assertEqual(self.symbol("AB09"), ord("."))
                self.update(name, False)
                self.assertEqual(self.modifiers(), 0)

    def test_right_command_preserves_other_held_modifiers(self):
        for modifier in ("LFSH", "LCTL", "LWIN", "CAPS", "LALT", "RALT"):
            with self.subTest(modifier=modifier):
                self.update(modifier, True)
                expected = self.modifiers()
                self.assertNotEqual(expected, 0)
                self.update("RWIN", True)
                self.assertEqual(self.symbol("RWIN"), ESCAPE)
                self.assertEqual(self.modifiers(), expected)
                self.update("RWIN", False)
                self.assertEqual(self.modifiers(), expected)
                self.update(modifier, False)
                self.assertEqual(self.modifiers(), 0)

    def test_left_command_remains_super(self):
        self.assertEqual(self.symbol("LWIN"), 0xFFEB)  # Super_L
        self.update("LWIN", True)
        self.assertEqual(
            self.xkb.xkb_state_mod_name_is_active(self.state, b"Mod4", EFFECTIVE), 1,
        )
        self.update("LWIN", False)
        self.assertEqual(self.modifiers(), 0)

    def test_caps_remains_super_and_does_not_toggle_caps_lock(self):
        self.assertEqual(self.symbol("CAPS"), 0xFFEB)  # Super_L
        self.update("CAPS", True)
        self.assertEqual(
            self.xkb.xkb_state_mod_name_is_active(self.state, b"Mod4", EFFECTIVE), 1,
        )
        self.update("CAPS", False)
        self.assertEqual(self.modifiers(), 0)
        self.assertEqual(self.symbol("AC01"), ord("a"))

    def test_original_escape_and_shifted_letters_are_unchanged(self):
        self.assertEqual(self.symbol("ESC"), ESCAPE)
        self.assertEqual(self.symbol("AC01"), ord("a"))
        self.update("LFSH", True)
        self.assertEqual(self.symbol("AC01"), ord("A"))


class KeyboardConfigurationTest(unittest.TestCase):
    def test_keymap_is_in_deployment_manifest(self):
        manifest = (ROOT / "setup/home-files.txt").read_text().splitlines()
        self.assertIn(str(KEYMAP.relative_to(ROOT)), manifest)
        self.assertNotIn(".config/hypr/option-escape.xkb", manifest)

    def test_input_loads_the_keymap_with_caps_super_as_fallback(self):
        lua = shutil.which("lua")
        if lua is None:
            self.skipTest("Lua is not installed")
        script = '''
local config
hl = {
    config = function(value) config = value end,
    gesture = function() end,
}
dofile(arg[1])
assert(config.input.kb_file == os.getenv("HOME") .. "/.config/hypr/keyboard.xkb")
assert(config.input.kb_options == "caps:super")
assert(config.input.kb_layout == "us")
'''
        result = subprocess.run(
            [lua, "-", str(ROOT / ".config/hypr/input.lua")],
            input=script, text=True, capture_output=True, timeout=5,
            env={**os.environ, "HOME": "/example/home with spaces"},
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
