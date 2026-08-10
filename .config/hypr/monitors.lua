
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
    scale    = 1.6,
})

-- keybindings.lua binds SUPER+L to resize_monitor and SUPER+SHIFT+L to
-- resize_monitor_2x as global function references (same pattern as the real config).
-- 1.6x is this panel's default/base scale. Both binds are toggles against their own
-- target, relative to that base: press when not at the target -> jump to the target;
-- press again while at the target -> drop back to the 1.6x base.
local current_scale = 1.6

local function set_scale(scale)
    hl.monitor({
        output   = "eDP-1",
        mode     = "2560x1600@60",
        position = "auto",
        scale    = scale,
    })
    current_scale = scale
end

function resize_monitor()
    if current_scale ~= 1 then
        set_scale(1)
    else
        set_scale(1.6)
    end
end

function resize_monitor_2x()
    if current_scale ~= 2 then
        set_scale(2)
    else
        set_scale(1.6)
    end
end
