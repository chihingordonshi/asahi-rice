"""Validate Noctalia configuration and run bar logic without touching the desktop."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".config/hypr/noctalia-shell.lua"
CONFIG = tomllib.loads((ROOT / ".config/noctalia/config.toml").read_text())
LUAJIT = shutil.which("luajit")


class NoctaliaSetupTest(unittest.TestCase):
    def test_layout_and_native_popups(self):
        bar = CONFIG["bar"]["default"]
        self.assertEqual(bar["thickness"], 36)
        self.assertEqual(bar["start"], ["suspend", "kill", "cpu", "memory", "power_profile", "workspaces"])
        self.assertEqual(bar["center"], ["clock"])
        self.assertEqual(bar["end"], ["tray", "ibus_restart", "wallpaper", "brightness", "volume", "bluetooth", "network", "battery"])
        self.assertNotIn("ibus", CONFIG["widget"])
        self.assertEqual(CONFIG["widget"]["network"]["actions"]["left"], "panel-toggle control-center network")
        # Missing overrides deliberately select Noctalia's native audio/BT panels.
        self.assertNotIn("left", CONFIG["widget"]["volume"]["actions"])
        self.assertNotIn("actions", CONFIG["widget"]["bluetooth"])
        self.assertFalse(bar["smart_auto_hide"])
        self.assertFalse(bar["auto_hide"])
        self.assertFalse(bar["show_on_workspace_switch"])
        self.assertFalse(bar["reserve_space"])
        self.assertEqual(bar["auto_hide_delay_ms"], 0)
        self.assertFalse(CONFIG["shell"]["animation"]["enabled"])
        for name in ("brightness", "volume"):
            self.assertIn("waybar-level", CONFIG["widget"][name]["actions"]["scroll_up"])
        self.assertTrue(CONFIG["audio"]["enable_overdrive"])

    def test_ibus_restart_button_and_helper_deployment(self):
        button = CONFIG["widget"]["ibus_restart"]
        self.assertEqual(button["type"], "custom_button")
        self.assertEqual(button["glyph"], "keyboard")
        self.assertEqual(button["actions"], {"left": "exec ~/.local/bin/ibus-restart"})
        self.assertIn("unfinished composition", button["tooltip"])
        files = (ROOT / "setup/home-files.txt").read_text().splitlines()
        self.assertIn(".local/bin/ibus-restart", files)
        self.assertTrue(os.access(ROOT / ".local/bin/ibus-restart", os.X_OK))

    def test_wallpaper_rotation_and_minimal_services(self):
        button = CONFIG["widget"]["wallpaper"]
        self.assertEqual(button["type"], "custom_button")
        self.assertEqual(button["glyph"], "wallpaper")
        self.assertEqual(button["actions"], {"left": "wallpaper-random"})
        wallpaper = CONFIG["wallpaper"]
        self.assertTrue(wallpaper["enabled"])
        self.assertTrue(wallpaper["directory"].endswith("/Pictures/Wallpapers"))
        self.assertEqual(wallpaper["automation"], {"enabled": True, "interval_seconds": 900, "order": "random", "recursive": True})
        self.assertFalse(CONFIG["notification"]["enable_daemon"])
        self.assertFalse(CONFIG["osd"]["enabled"])
        self.assertFalse(CONFIG["lockscreen"]["enabled"])
        self.assertFalse(CONFIG["theme"]["templates"]["enable_builtin_templates"])
        self.assertFalse(CONFIG["theme"]["templates"]["enable_community_templates"])
        self.assertEqual(CONFIG["plugins"]["enabled"], [])

    def test_native_launcher_and_capture_bindings(self):
        binds = (ROOT / ".config/hypr/keybindings.lua").read_text()
        for key, command in (
            ("D", "panel-toggle launcher"),
            ("A", "screenshot-region"),
            ("SHIFT + A", "screenshot-fullscreen all"),
        ):
            self.assertRegex(
                binds,
                rf'hl\.bind\(mainMod \.\. " \+ {re.escape(key)}",\s*'
                rf'hl\.dsp\.exec_cmd\("noctalia msg {command}"\)\)',
            )
        self.assertNotIn("rofi", binds)
        self.assertNotIn("mac-screenshot", binds)

    def test_native_capture_saves_and_copies_without_extra_tools(self):
        capture = CONFIG["shell"]["screenshot"]
        self.assertTrue(capture["directory"].endswith("/Pictures/Screenshots"))
        self.assertEqual(capture["filename_pattern"], "Screenshot %Y-%m-%d at %H.%M.%S")
        self.assertEqual(capture["format"], "png")
        self.assertTrue(capture["save_to_file"])
        self.assertTrue(capture["copy_to_clipboard"])
        for option in ("pipe_to_command", "annotate", "confirm_region", "show_cursor"):
            self.assertFalse(capture[option])
        files = (ROOT / "setup/home-files.txt").read_text().splitlines()
        for obsolete in (".config/rofi/config.rasi", ".config/fuzzel/fuzzel.ini", ".local/bin/mac-screenshot"):
            self.assertNotIn(obsolete, files)
            self.assertFalse((ROOT / obsolete).exists())

    def test_palette_has_both_required_variants(self):
        palette = json.loads((ROOT / ".config/noctalia/palettes/Waybar.json").read_text())
        for mode in ("dark", "light"):
            self.assertEqual(palette[mode]["mSurface"], "#131317")
            self.assertEqual(palette[mode]["mOnSurface"], "#e5e1e7")
            self.assertEqual(palette[mode]["mPrimary"], "#c2c1ff")
            self.assertEqual(len(palette[mode]), 16)

    def test_deployment_has_one_startup_owner_and_no_generated_module_dependency(self):
        main = (ROOT / ".config/hypr/hyprland.lua").read_text()
        startup = (ROOT / ".config/hypr/autostart.lua").read_text()
        binds = (ROOT / ".config/hypr/keybindings.lua").read_text()
        services = (ROOT / "setup/user-services.txt").read_text().splitlines()
        files = (ROOT / "setup/home-files.txt").read_text().splitlines()
        self.assertIn('require("noctalia-shell")', main)
        self.assertNotIn('require("noctalia")', main)
        self.assertNotIn('require("waybar")', main)
        self.assertEqual(startup.count('hl.exec_cmd("noctalia")'), 1)
        self.assertNotIn('start waybar.service', startup)
        self.assertNotIn('waybar.service', services)
        # The secondary bar shortcut is customizable independently of this setup.
        self.assertIn('hl.bind(mainMod .. " + X", ToggleNoctaliaVisibility)', binds)
        self.assertIn('ibus-language toggle', binds)
        for path in (".config/noctalia/config.toml", ".config/noctalia/palettes/Waybar.json", ".config/hypr/noctalia-shell.lua", ".local/bin/noctalia-bar-apply"):
            self.assertIn(path, files)
        self.assertIn('noctalia', (ROOT / "setup/dnf-packages.txt").read_text().splitlines())


HARNESS = r'''
local script = arg[1]
local workspace = { id = 1 }
local special = nil
local windows = { { workspace = workspace, mapped = true, hidden = false, floating = false } }
local layers = { { pid = 123 } }
local wallpaperLayers = {}
local timers, subscriptions, commands, reservations = {}, {}, {}, {}
hl = {
    layer_rule = function() end,
    window_rule = function() end,
    get_layers = function(filter)
        if filter.namespace == "noctalia-bar-default" then return layers end
        assert(filter.namespace == "noctalia-wallpaper")
        return wallpaperLayers
    end,
    get_active_workspace = function() return workspace end,
    get_active_special_workspace = function() return special end,
    get_windows = function(filter)
        assert(filter.mapped == true and filter.floating == false)
        local result = {}
        for _, w in ipairs(windows) do
            if w.workspace == filter.workspace and w.mapped and not w.floating then
                result[#result + 1] = w
            end
        end
        return result
    end,
    exec_cmd = function(command)
        assert(command:find("/.local/bin/noctalia-bar-apply' >/dev/null", 1, true), "unexpected command: " .. command)
        local file = assert(io.open(os.getenv("XDG_RUNTIME_DIR") .. "/noctalia-bar.desired"))
        local reserve, visibility = file:read("*a"):match("^(%a+) (%a+)\n$")
        file:close()
        assert(reserve == "true" or reserve == "false")
        assert(visibility == "show" or visibility == "hide")
        commands[#commands + 1] = visibility
        reservations[#reservations + 1] = reserve == "true"
    end,
    timer = function(callback, options)
        assert(options.timeout == 200 and options.type == "repeat")
        local timer = { callback = callback, enabled = true }
        function timer:set_enabled(value) self.enabled = value end
        timers[#timers + 1] = timer
        return timer
    end,
    on = function(event, callback)
        assert(event == "config.unload" or event == "workspace.active" or event == "workspace.special_active")
        local subscription = { event = event, callback = callback, active = true }
        function subscription:remove() self.active = false end
        subscriptions[#subscriptions + 1] = subscription
        return subscription
    end,
}
local function activeTimers()
    local n = 0
    for _, t in ipairs(timers) do if t.enabled then n = n + 1 end end
    return n
end
local function load()
    dofile(script)
    assert(activeTimers() == 1, "duplicate bar controller")
end
local function tick()
    for _, t in ipairs(timers) do if t.enabled then t.callback() end end
end
local function visibility(expected)
    assert(commands[#commands] == expected, "unexpected bar visibility")
end
local function count(expected)
    assert(#commands == expected, "expected " .. expected .. " commands, got " .. #commands)
end
local function event(name)
    for _, s in ipairs(subscriptions) do
        if s.active and s.event == name then s.callback() end
    end
end
local function setPinnedOnDisk(value)
    local path = os.getenv("XDG_RUNTIME_DIR") .. "/noctalia-bar.force-show"
    if value then
        local file = assert(io.open(path, "w"))
        file:close()
    else
        os.remove(path)
    end
end
local function reload()
    event("config.unload")
    assert(activeTimers() == 0)
    NoctaliaBarController = nil
    load()
end
'''


@unittest.skipUnless(LUAJIT, "luajit is required for mocked bar-controller tests")
class NoctaliaBarTest(unittest.TestCase):
    def run_lua(self, scenario):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="noctalia-bar-", dir=artifacts) as directory:
            result = subprocess.run(
                [LUAJIT, "-", str(SCRIPT)], input=HARNESS + "\n" + scenario,
                env={**os.environ, "XDG_RUNTIME_DIR": directory},
                text=True, capture_output=True, timeout=5,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tiled_windows_hide_without_periodic_processes(self):
        self.run_lua('''
            load(); visibility("hide"); count(1)
            for _ = 1, 100 do tick() end
            count(1)
        ''')

    def test_empty_and_floating_only_workspaces_stay_visible(self):
        self.run_lua('''
            windows = {}; load(); visibility("show"); count(1)
            windows = {{ workspace = workspace, mapped = true, floating = true }}
            tick(); visibility("show"); count(1)
            windows[2] = {workspace = workspace, mapped = true, floating = false}
            tick(); visibility("hide"); count(2)
            windows[2].floating = true
            tick(); visibility("show"); count(3)
        ''')

    def test_hidden_unmapped_and_other_workspace_windows_do_not_hide(self):
        self.run_lua('''
            windows = {
                { workspace = workspace, mapped = true, hidden = true },
                { workspace = workspace, mapped = false },
                { workspace = {id=2}, mapped = true },
            }
            load(); visibility("show")
        ''')

    def test_workspace_changes_and_special_workspaces(self):
        self.run_lua('''
            load(); visibility("hide")
            local original = workspace
            workspace = {id=2}; tick(); visibility("show")
            workspace = original; tick(); visibility("hide")
            special = {id=-99}; tick(); visibility("show")
            windows[2] = {workspace=special, mapped=true, floating=true}
            tick(); visibility("show")
            windows[2].floating = false; tick(); visibility("hide")
            special = nil; tick(); visibility("hide"); count(5)
        ''')

    def test_toggle_show_stays_pinned_across_polling_and_workspace_events(self):
        self.run_lua('''
            load(); visibility("hide"); count(1)
            ToggleNoctaliaVisibility(); visibility("show"); count(2)
            assert(reservations[2] == true)
            local file = assert(io.open(os.getenv("XDG_RUNTIME_DIR") .. "/noctalia-bar.force-show"))
            file:close()
            for _ = 1, 100 do tick() end
            event("workspace.active")
            special = {id=-99}
            windows[2] = {workspace=special, mapped=true, floating=false}
            event("workspace.special_active"); visibility("show"); count(2)
            reload(); visibility("show"); count(3)
            assert(reservations[3] == true)
            ToggleNoctaliaVisibility(); visibility("hide"); count(4)
            assert(reservations[4] == false)
            assert(not io.open(os.getenv("XDG_RUNTIME_DIR") .. "/noctalia-bar.force-show"))
            for _ = 1, 100 do tick() end
            count(4)
        ''')

    def test_unpin_resamples_current_windows_and_special_workspace(self):
        self.run_lua('''
            load(); visibility("hide"); count(1)
            ToggleNoctaliaVisibility(); visibility("show"); count(2)
            windows[1].floating = true
            ToggleNoctaliaVisibility(); visibility("show"); count(3)
            assert(reservations[3] == false)
            ToggleNoctaliaVisibility(); visibility("show"); count(4)
            windows[1].floating = false
            ToggleNoctaliaVisibility(); visibility("hide"); count(5)
            ToggleNoctaliaVisibility(); visibility("show"); count(6)
            special = {id=-99}
            ToggleNoctaliaVisibility(); visibility("show"); count(7)
            ToggleNoctaliaVisibility(); visibility("show"); count(8)
            windows[2] = {workspace=special, mapped=true, floating=false}
            ToggleNoctaliaVisibility(); visibility("hide"); count(9)
            ToggleNoctaliaVisibility(); visibility("show"); count(10)
            windows[2].hidden = true
            ToggleNoctaliaVisibility(); visibility("show"); count(11)
        ''')

    def test_toggle_waits_for_shell_and_ignores_stopped_controller(self):
        self.run_lua('''
            layers = {}; load(); count(0)
            ToggleNoctaliaVisibility(); count(0)
            assert(NoctaliaBarController.pinned == true)
            wallpaperLayers = {{pid=123}}; tick(); visibility("show"); count(1)
            ToggleNoctaliaVisibility(); visibility("hide"); count(2)
            NoctaliaBarController.stop()
            ToggleNoctaliaVisibility(); tick(); count(2)
            assert(NoctaliaBarController.pinned == false)
            assert(not io.open(os.getenv("XDG_RUNTIME_DIR") .. "/noctalia-bar.force-show"))
        ''')

    def test_existing_pin_survives_reload_and_can_be_unpinned(self):
        self.run_lua('''
            setPinnedOnDisk(true); load(); visibility("show"); count(1)
            reload(); visibility("show"); count(2)
            assert(reservations[2] == true)
            ToggleNoctaliaVisibility(); visibility("hide"); count(3)
            assert(reservations[3] == false)
            reload(); visibility("hide"); count(4)
            windows[1].floating = true; tick(); visibility("show"); count(5)
        ''')

    def test_shell_startup_restart_and_hidden_layer_disappearance(self):
        self.run_lua('''
            layers = {}; load(); count(0)
            layers = {{pid=123}}; tick(); visibility("hide"); count(1)
            layers = {}; tick(); count(1)
            windows[1].floating = true; tick(); visibility("show"); count(2)
            layers = {{pid=124}}; tick(); visibility("show"); count(3)
            for _ = 1, 10 do tick() end
            count(3)
        ''')

    def test_pin_reserves_space_even_when_floating_only_bar_is_already_shown(self):
        self.run_lua('''
            windows[1].floating = true
            load(); visibility("show"); assert(reservations[1] == false)
            ToggleNoctaliaVisibility(); visibility("show"); count(2)
            assert(reservations[2] == true)
            reload(); visibility("show"); assert(reservations[3] == true)
            ToggleNoctaliaVisibility(); visibility("show"); count(4)
            assert(reservations[4] == false)
            layers = {{pid=124}}; tick(); count(5)
            assert(reservations[5] == false)
        ''')

    def test_workspace_switches_reconcile_without_waiting_for_timer(self):
        self.run_lua('''
            local empty = {id=2}
            local occupied = workspace
            workspace = empty; load(); visibility("show")
            workspace = occupied; event("workspace.active"); visibility("hide"); count(2)
            special = empty; event("workspace.special_active"); visibility("show"); count(3)
            special = nil; event("workspace.special_active"); visibility("hide"); count(4)
            NoctaliaBarController.stop()
            event("workspace.active"); count(4)
        ''')

    def test_hidden_bar_reload_and_restart_use_wallpaper_for_discovery(self):
        self.run_lua('''
            load(); visibility("hide"); count(1)
            layers = {}; wallpaperLayers = {{pid=123}}
            reload(); visibility("hide"); count(2)
            for _ = 1, 10 do tick() end
            count(2)
            ToggleNoctaliaVisibility(); visibility("show"); count(3)
            assert(reservations[3] == true)
            ToggleNoctaliaVisibility(); visibility("hide"); count(4)
            wallpaperLayers = {{pid=124}}
            tick(); visibility("hide"); count(5)
            windows = {}; event("workspace.active"); visibility("show"); count(6)
        ''')

    def test_duplicate_load_unload_and_missing_workspace(self):
        self.run_lua('''
            load(); load(); assert(activeTimers() == 1)
            workspace = nil; tick(); visibility("show")
            NoctaliaBarController.stop(); assert(activeTimers() == 0)
            local n = #commands; tick(); count(n)
        ''')


if __name__ == "__main__":
    unittest.main()
