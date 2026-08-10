
------------------
---- MONITORS ----
------------------

-- Hardware pinned to this machine's actual detected display (via `hyprctl monitors -j`),
-- not copied from the XPS16's monitors.lua (which was 1920x1200@120 for a completely
-- different panel) and not left on "preferred/auto" guesses.
hl.monitor({
    output   = "eDP-1",
    mode     = "2560x1600@60",
    position = "auto",
    scale    = 2,
})

-- keybindings.lua binds SUPER+L to resize_monitor as a global function reference (same
-- as the real config) -- adapted here to toggle native scale vs a lower integer scale,
-- since this machine only has the one built-in panel (no second-monitor mode to cycle
-- like the XPS16's laptop+external setup).
local monitor_mode = 0

function resize_monitor()
    if monitor_mode == 0 then
        hl.monitor({
            output   = "eDP-1",
            mode     = "2560x1600@60",
            position = "auto",
            scale    = 1,
        })
        monitor_mode = 1
    else
        hl.monitor({
            output   = "eDP-1",
            mode     = "2560x1600@60",
            position = "auto",
            scale    = 2,
        })
        monitor_mode = 0
    end
end
