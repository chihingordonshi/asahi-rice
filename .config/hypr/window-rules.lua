
--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- and https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/

local suppressMaximizeRule = hl.window_rule({
    name  = "suppress-maximize-events",
    match = { class = ".*" },

    suppress_event = "maximize",
})

hl.window_rule({
    name  = "fix-xwayland-drags",
    match = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
    },

    no_focus = true,
})

-- Hyprland-run windowrule
hl.window_rule({
    name  = "move-hyprland-run",
    match = { class = "hyprland-run" },

    move  = "20 monitor_h-120",
    float = true,
})

-- Spacer window that is invisible but ocupies space
hl.window_rule({
    name = "spacer-window",
    match = {
        class = "spacer"
    },
    border_size = 0,
    tile = true,
    opacity = 0.0,
    min_size = { "monitor_w * 0.1", "monitor_h * 0.1" }
})

hl.window_rule({
    name = "terminal",
    match = {
        class = "terminal"
    },
    opaque = true,
})

hl.window_rule({
    name = "cover-screen-borderless",
    match = { tag = "cover-screen" },
    border_size = 0,
    rounding = 0,
    no_shadow = true,
})

hl.window_rule({
    name = "wifi-select-float",
    match = {
        class = "wifi-select"
    },
    float = true,
    opaque = true,
})

hl.window_rule({
    name = "wechat-tile",
    match = {
        class = "[Ww]e[Cc]hat"
    },
    tile = true,
})

hl.window_rule({
    name = "sticky",
    match = {
        class = "sticky"
    },
    float = true,
    size = {300, 300},
    move = {"(cursor_x - 150)", "(cursor_y - 150)"},
    opaque = true,
})


