"""Run the native controller with mocked Hyprland/procfs, never the live session."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".config/hypr/waybar.lua"
LUAJIT = shutil.which("luajit")

HARNESS = r'''
local script = arg[1]
local now = 10000
local workspace = { windows = 1 }
local cursor, monitor = { x = 100, y = 300 }, { y = 0 }
local alive = { [123] = "456" }
local layers = { { pid = 123 } }
local timers, subscriptions, signals = {}, {}, {}
local realOpen = io.open
local function fakeFile(contents)
    return { read = function() return contents end, close = function() end }
end
io.open = function(path, mode)
    if path == "/proc/uptime" then
        return fakeFile(string.format("%.3f 0\n", now / 1000))
    end
    local pid = path:match("^/proc/(%d+)/stat$")
    if pid then
        local start = alive[tonumber(pid)]
        if not start then return nil end
        return fakeFile(pid .. " (waybar) S " .. string.rep("0 ", 18) .. start .. " 0\n")
    end
    return realOpen(path, mode)
end
hl = {
    get_layers = function(filter)
        assert(filter.namespace == "waybar")
        return layers
    end,
    get_active_workspace = function() return workspace end,
    get_cursor_pos = function() return cursor end,
    get_monitor_at_cursor = function() return monitor end,
    exec_cmd = function(command)
        local pid = command:match("^kill %-USR1 (%d+)$")
        assert(pid, "unexpected external command: " .. command)
        signals[#signals + 1] = tonumber(pid)
    end,
    timer = function(callback, options)
        assert(options.timeout == 100 and options.type == "repeat")
        local timer = { callback = callback, enabled = true }
        function timer:set_enabled(value) self.enabled = value end
        timers[#timers + 1] = timer
        return timer
    end,
    on = function(event, callback)
        assert(event == "config.unload")
        local subscription = { callback = callback, active = true }
        function subscription:remove() self.active = false end
        subscriptions[#subscriptions + 1] = subscription
        return subscription
    end,
}
local function activeTimers()
    local count = 0
    for _, timer in ipairs(timers) do
        if timer.enabled then count = count + 1 end
    end
    return count
end
local function load()
    dofile(script)
    assert(activeTimers() == 1, "duplicate polling controller")
end
local function advance(milliseconds)
    now = now + milliseconds
    for _, timer in ipairs(timers) do
        if timer.enabled then timer.callback() end
    end
end
local function reload()
    for _, subscription in ipairs(subscriptions) do
        if subscription.active then subscription.callback() end
    end
    assert(activeTimers() == 0)
    -- Hyprland creates a fresh Lua state on config reload. No globals survive.
    WaybarAutohideController = nil
    load()
end
local function count(expected)
    assert(#signals == expected, "expected " .. expected .. " signals, got " .. #signals)
end
local function hidden()
    load()
    advance(1000)
    count(1)
    assert(signals[1] == 123)
end
local forceFile = os.getenv("XDG_RUNTIME_DIR") .. "/waybar-autohide.force-show"
local function externalForce(enabled)
    if enabled then
        local file = assert(realOpen(forceFile, "w"))
        file:close()
    else
        os.remove(forceFile)
    end
end
'''


@unittest.skipUnless(LUAJIT, "luajit is required for mocked native-controller tests")
class WaybarAutohideTest(unittest.TestCase):
    def run_lua(self, scenario):
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="waybar-autohide-", dir=artifacts) as directory:
            result = subprocess.run(
                [LUAJIT, "-", str(SCRIPT)],
                input=HARNESS + "\n" + scenario,
                env={**os.environ, "XDG_RUNTIME_DIR": directory},
                text=True, capture_output=True, timeout=5,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_startup_grace_and_no_periodic_external_processes(self):
        self.run_lua('''
            load()
            advance(999)
            count(0)
            advance(1)
            count(1)
            for _ = 1, 100 do advance(100) end
            count(1)
        ''')

    def test_empty_workspace_forces_show(self):
        self.run_lua('''
            hidden()
            workspace.windows = 0
            advance(100)
            count(2)
            for _ = 1, 10 do advance(100) end
            count(2)
            workspace.windows = 1
            advance(100)
            count(3)
        ''')

    def test_edge_delay_cancels_on_leave_and_hover_has_72px_boundary(self):
        self.run_lua('''
            hidden()
            cursor.y = 0
            advance(100)
            advance(199)
            count(1)
            cursor.y = 1
            advance(1)
            count(1)
            cursor.y = 0
            advance(100)
            advance(199)
            count(1)
            advance(1)
            count(2)
            cursor.y = 71.9
            advance(100)
            count(2)
            cursor.y = 72
            advance(100)
            count(3)
        ''')

    def test_monitor_relative_edge_and_missing_cursor_are_safe(self):
        self.run_lua('''
            hidden()
            monitor.y = -1000
            cursor.y = -1000
            advance(100)
            advance(200)
            count(2)
            cursor.y = -929
            advance(100)
            count(2)
            cursor.y = -928
            advance(100)
            count(3)
            cursor.y = -1000
            advance(100)
            cursor = nil
            advance(200)
            count(3)
            cursor = { y = -1000 }
            advance(100)
            advance(199)
            count(3)
            advance(1)
            count(4)
        ''')

    def test_force_override_and_legacy_toggle_file(self):
        self.run_lua('''
            hidden()
            ToggleWaybarVisibility()
            count(2)
            for _ = 1, 10 do advance(100) end
            count(2)
            reload()
            count(2)
            ToggleWaybarVisibility()
            count(3)
            externalForce(true)
            advance(100)
            count(4)
            externalForce(false)
            advance(100)
            count(5)
        ''')

    def test_reload_preserves_hidden_visible_and_startup_state(self):
        self.run_lua('''
            load()
            advance(500)
            reload()
            advance(499)
            count(0)
            advance(1)
            count(1)
            reload()
            advance(100)
            count(1)
            workspace.windows = 0
            advance(100)
            count(2)
            reload()
            count(2)
            workspace.windows = 1
            advance(100)
            count(3)
        ''')

    def test_duplicate_load_retains_exactly_one_controller(self):
        self.run_lua('''
            hidden()
            load()
            advance(100)
            count(1)
            ToggleWaybarVisibility()
            count(2)
            assert(activeTimers() == 1)
        ''')

    def test_new_pid_and_pid_reuse_get_fresh_startup_grace(self):
        self.run_lua('''
            hidden()
            alive[123] = nil
            alive[234] = "567"
            layers = { { pid = 234 }, { pid = 234 } }
            advance(100)
            count(1)
            advance(999)
            count(1)
            advance(1)
            count(2)
            assert(signals[2] == 234)
            alive[234] = "890"
            advance(100)
            advance(999)
            count(2)
            advance(1)
            count(3)
            assert(signals[3] == 234)
        ''')

    def test_hidden_layer_disappearance_does_not_mean_a_process_restart(self):
        self.run_lua('''
            hidden()
            layers = {}
            advance(100)
            reload()
            count(1)
            ToggleWaybarVisibility()
            count(2)
            alive[123] = nil
            advance(100)
            ToggleWaybarVisibility()
            count(2)
        ''')

    def test_missing_workspace_preserves_visibility(self):
        self.run_lua('''
            hidden()
            workspace = nil
            cursor.y = 0
            advance(100)
            advance(1000)
            count(1)
            workspace = { windows = 0 }
            advance(100)
            count(2)
        ''')


if __name__ == "__main__":
    unittest.main()
