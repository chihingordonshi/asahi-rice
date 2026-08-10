
---------------------
---- KEYBINDINGS ----
---------------------

local mainMod = "SUPER" -- Sets "Windows" key as main modifier

-- Example binds, see https://wiki.hypr.land/Configuring/Basics/Binds/ for more
hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd("kitty --class terminal"))
local closeWindowBind = hl.bind(mainMod .. " + C", hl.dsp.window.close())
-- closeWindowBind:set_enabled(false)
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + F", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + R", NoTransparency)
hl.bind(mainMod .. " + P", hl.dsp.window.pseudo())
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"))    -- dwindle only
hl.bind(mainMod .. " + L", resize_monitor)
hl.bind(mainMod .. " + SHIFT + L", resize_monitor_2x)

-- Move focus with mainMod + arrow keys
hl.bind(mainMod .. " + left",  hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

-- Switch workspaces with mainMod + [0-9]
-- Move active window to a workspace with mainMod + SHIFT + [0-9]
for i = 1, 10 do
    local key = i % 10 -- 10 maps to key 0
    hl.bind(mainMod .. " + " .. key,             hl.dsp.focus({ workspace = i}))
    hl.bind(mainMod .. " + SHIFT + " .. key,     hl.dsp.window.move({ workspace = i }))
end

-- Example special workspace (scratchpad)
hl.bind(mainMod .. " + S",         hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

-- Scroll through existing workspaces with mainMod + scroll
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Move/resize windows with mainMod + LMB/RMB and dragging
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Resize windows with mainMod + Shift + Arrowkey
hl.bind(mainMod .. " + SHIFT + left", hl.dsp.window.resize({ x = -25, y = 0, relative = true }), {repeating = true})
hl.bind(mainMod .. " + SHIFT + right", hl.dsp.window.resize({ x = 25, y = 0, relative = true }), {repeating = true})
hl.bind(mainMod .. " + SHIFT + up", hl.dsp.window.resize({ x = 0, y = -15, relative = true }), {repeating = true})
hl.bind(mainMod .. " + SHIFT + down", hl.dsp.window.resize({ x = 0, y = 15, relative = true }), {repeating = true})

-- Laptop multimedia keys for volume and LCD brightness
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      { locked = true, repeating = true })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     { locked = true, repeating = true })
hl.bind("XF86AudioMicMute",     hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),   { locked = true, repeating = true })
hl.bind("XF86MonBrightnessUp",  hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"),                  { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown",hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"),                  { locked = true, repeating = true })

-- Requires playerctl
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })

-- Screenshot (Mac-style: Print = region select, like Cmd+Shift+4)
local macScreenshot = os.getenv("HOME") .. "/.local/bin/mac-screenshot"
hl.bind("Print",             hl.dsp.exec_cmd(macScreenshot .. " region"))
hl.bind("SHIFT + Print",     hl.dsp.exec_cmd(macScreenshot .. " full"))    -- like Cmd+Shift+3
hl.bind(mainMod .. " + Print", hl.dsp.exec_cmd(macScreenshot .. " window")) -- active window
hl.bind("CTRL + Print",      hl.dsp.exec_cmd("screengrab"))             -- full GUI tool

-- Create spacer window with mainMod + N
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("kitty --class spacer &"))

-- Open browser with mainMod + W
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd(browser))

-- App launcher with mainMod + D (real config calls caelestia's own launcher drawer,
-- not viable here since caelestia isn't installed -- rofi installed and bound instead)
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd("rofi -show drun"))

-- Spawn a new sticky note (dbus-activates the sticky app if not already
-- running; never shows the notes manager/control panel, see show-manager
-- gsetting in org.x.sticky)
hl.bind(mainMod .. " + V", hl.dsp.exec_cmd("gdbus call --session --dest org.x.sticky --object-path /org/x/sticky --method org.x.sticky.NewNoteBlank"))
