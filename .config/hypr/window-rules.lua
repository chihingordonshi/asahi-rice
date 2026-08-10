
--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- and https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/

-- Example window rules that are useful

local suppressMaximizeRule = hl.window_rule({
    -- Ignore maximize requests from all apps. You'll probably like this.
    name  = "suppress-maximize-events",
    match = { class = ".*" },

    suppress_event = "maximize",
})
-- suppressMaximizeRule:set_enabled(false)

hl.window_rule({
    -- Fix some dragging issues with XWayland
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

-- Layer rules also return a handle.
-- local overlayLayerRule = hl.layer_rule({
--     name  = "no-anim-overlay",
--     match = { namespace = "^my-overlay$" },
--     no_anim = true,
-- })
-- overlayLayerRule:set_enabled(false)

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

-- WeChat runs as the com.tencent.WeChat flatpak now (not the wechat-bin
-- XWayland binary the old comment here assumed -- that class never
-- matched, which is why this rule silently did nothing). Its
-- auto-float heuristic (or _KDE_NET_WM_WINDOW_TYPE_OVERRIDE under
-- XWayland, if that build ever comes back) forces it floating even
-- though its size hints allow tiling. Override that; regex covers both
-- the flatpak app-id and the old lowercase class just in case.
hl.window_rule({
    name = "wechat-tile",
    match = {
        class = "[Ww]e[Cc]hat"
    },
    tile = true,
})

-- sticky notes app: always float, never tile
hl.window_rule({
    name = "sticky-notes-float",
    match = {
        class = "sticky.py"
    },
    float = true,
})

-- sticky's internal helper window (title "Notes", used only as a hidden
-- 1x1 parent for dialogs) would otherwise render as a blank floating
-- window; shrink it to nothing and keep it out of the way
hl.window_rule({
    name = "sticky-hide-helper-window",
    match = {
        class = "sticky.py",
        title = "^Notes$",
    },
    size     = "1 1",
    opacity  = 0.0,
    no_focus = true,
})
