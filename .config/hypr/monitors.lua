
------------------
---- MONITORS ----
------------------

hl.monitor({
    output   = "eDP-1",
    mode     = "2560x1600@60",
    position = "auto",
    scale    = 1.6,
})

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
