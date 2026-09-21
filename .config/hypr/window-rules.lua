
--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- and https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/

hl.window_rule({
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

-- XWayland popups are often implemented as floating windows with transparent
-- padding.  Do not blur through that padding, so it remains fully transparent.
hl.window_rule({
    name = "no-blur-xwayland-floats",
    match = {
        xwayland = true,
        float    = true,
    },

    border_size = 0,
    no_blur     = true,
    no_shadow   = true,
})

-- Hyprland Run launcher
hl.window_rule({
    name  = "move-hyprland-run",
    match = { class = "hyprland-run" },

    move  = "20 monitor_h-120",
    float = true,
})

-- Invisible tiled window that occupies space
hl.window_rule({
    name        = "spacer-window",
    match       = { class = "spacer" },
    border_size = 0,
    tile        = true,
    opacity     = 0.0,
    min_size    = { "monitor_w * 0.1", "monitor_h * 0.1" },
})

hl.window_rule({
    name   = "terminal",
    match  = { class = "terminal" },
    opaque = true,
})

hl.window_rule({
    name   = "wifi-select",
    match  = { class = "^wifi-select$" },
    float  = true,
    size   = { 800, 500 },
    opaque = true,
})

-- Keep GTK file chooser dialogs comfortably sized and centered.
hl.window_rule({
    name  = "gtk-file-chooser",
    match = { class = "^Xdg-desktop-portal-gtk$" },

    float  = true,
    size   = { 1000, 800 },
    center = true,
})

-- Randomized colored Kitty mosaic launched from Waybar. Keep every block in
-- the dwindle tree so Hyprland, rather than absolute coordinates, owns it.
hl.window_rule({
    name  = "abstract-kitty",
    match = { class = "^abstract-kitty$" },

    tile         = true,
    opaque       = true,
    border_size  = 2,
    border_color = "rgba(c4a7e7cc)",
    rounding     = 3,
    no_shadow    = true,
})


-- Dwindle is the sole tiled layout.
hl.window_rule({
    name = "single-dwindle-transparent-border",
    match = {
        float = false,
        workspace = "w[tv1]s[false]",
    },

    border_color = "rgba(00000000)",
    border_size  = 0,
    rounding    = 0,
    no_shadow   = true,
})

hl.window_rule({
    name  = "wechat-tile",
    match = { class = "[Ww]e[Cc]hat" },
    tile  = true,
})

hl.window_rule({
    name = "wechat-open-dialog-float",
    match = {
        class = "^[Ww]e[Cc]hat$",
        title = "^Open$",
    },
    float = true,
})

hl.window_rule({
    name   = "sticky",
    match  = { class = "sticky" },
    float  = true,
    size   = { 300, 300 },
    move   = { "(cursor_x - 150)", "(cursor_y - 150)" },
    opaque = true,
})

hl.window_rule({
    name = "zoom-webcam-popup",
    match = {
        class = "^brave-browser$",
        title = "^Gordon Shi's Zoom Meeting$",
    },
    float = true,
    size = { 336, 238 },
    move = { 1255, 44 },
})

function MoveWindowToWorkspace(workspace)
    local window = hl.get_active_window()
    if not window then
        return
    end

    hl.dispatch(hl.dsp.window.move({
        workspace = workspace,
        window = window,
        follow = true,
    }))
end
