
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

-- nmtui, launched from the waybar wifi module's on-click: floats centered as
-- a quick popup instead of tiling in with the rest of the workspace.
hl.window_rule({
    name = "wifi-select-float",
    match = {
        class = "wifi-select"
    },
    float = true,
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

-- sticky's internal helper window is a hidden 1x1 dummy window created once
-- at app startup to anchor dialogs. It can't be told apart from a real note
-- by class/title alone: the app never sets a native window title on notes
-- either, so both the dummy and every real note report title "Notes" to
-- Hyprland. A static title-matched rule (the old approach here) hid every
-- note along with the dummy. Instead, hide only the first sticky.py window
-- opened per process -- that's always the dummy, since it's created before
-- any note in the app's activation path.
local stickyDummySeenPids = {}
local stickyPrewarming = false

hl.on("window.open", function(win)
    if win.class ~= "sticky.py" then return end

    if not stickyDummySeenPids[win.pid] then
        stickyDummySeenPids[win.pid] = true

        -- opacity/no_blur/no_shadow only affect how it's drawn -- it's still
        -- a real mapped window on workspace 1, so it kept showing up (with a
        -- border) in waybar's workspace summary and the swipe-up overview.
        -- Parking it on its own special workspace removes it from workspace
        -- enumeration entirely, which is what those views actually key off
        -- (see waybar config.jsonc's ignore-workspaces and hypr-overview's
        -- clients filter, both matched on this same workspace name).
        hl.dispatch(hl.dsp.window.set_prop({ prop = "no_focus", value = 1, window = "address:" .. win.address }))
        hl.dispatch(hl.dsp.window.set_prop({ prop = "opacity",  value = 0, window = "address:" .. win.address }))
        hl.dispatch(hl.dsp.window.set_prop({ prop = "no_blur",   value = 1, window = "address:" .. win.address }))
        hl.dispatch(hl.dsp.window.set_prop({ prop = "no_shadow", value = 1, window = "address:" .. win.address }))
        hl.dispatch(hl.dsp.window.move({ workspace = "special:sticky-hidden", window = "address:" .. win.address }))
        return
    end

    -- Any further sticky.py window for a pid we've already seen the dummy
    -- for is a real note under normal use -- leave it alone. During the
    -- startup pre-warm below it would instead mean something unexpected
    -- came up alongside the dummy (e.g. a first-run import dialog); close
    -- it rather than let it sit around.
    if stickyPrewarming then
        -- kill, not close: close just sends a delete-event, which an app
        -- can intercept/ignore (e.g. sticky's manager hides itself on
        -- delete-event instead of actually closing) -- kill guarantees it's
        -- actually gone.
        hl.dispatch(hl.dsp.window.kill({ window = "address:" .. win.address }))
    end
end)

-- Pre-warm sticky at session start so the first Super+V of the session
-- (see keybindings.lua) doesn't pay for a cold dbus-activation launch.
-- Toggle to the hidden special workspace first, launch the app there (so
-- the dummy opens directly on it instead of relying on the move dispatch
-- above to relocate it after the fact), give it a couple seconds to settle,
-- then toggle back and return focus to workspace 1.
hl.on("hyprland.start", function()
    stickyPrewarming = true
    hl.dispatch(hl.dsp.workspace.toggle_special("sticky-hidden"))
    hl.exec_cmd("sticky")

    hl.timer(function()
        stickyPrewarming = false
        hl.dispatch(hl.dsp.workspace.toggle_special("sticky-hidden"))
        hl.dispatch(hl.dsp.focus({ workspace = 1 }))
    end, { timeout = 2000, type = "oneshot" })
end)
