
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

-- Enabled only while fullscreen mode is active.  Hyprland covers the monitor,
-- but client state 0 keeps applications such as Brave unaware that
-- they are fullscreen.
local fullscreenRule = hl.window_rule({
    name  = "fullscreen",
    match = {
        class = ".*",
        float = false,
        workspace = "s[false]",
    },

    fullscreen_state = "2 0",
    border_size      = 0,
    rounding         = 0,
    decorate         = false,
    no_anim          = true,
    no_blur          = true,
    no_dim           = true,
    no_shadow        = true,
    opacity          = "1.0 override 1.0 override 1.0 override",
    opaque           = true,
})
fullscreenRule:set_enabled(false)

local runtimeDir = os.getenv("XDG_RUNTIME_DIR") or "/tmp"
local fullscreenModeStateFile = runtimeDir .. "/hypr-fullscreen-mode"
os.remove(fullscreenModeStateFile)

local function setFullscreenModeState(enabled)
    if not enabled then
        os.remove(fullscreenModeStateFile)
        return
    end

    local stateFile = io.open(fullscreenModeStateFile, "w")
    if stateFile then
        stateFile:write("enabled\n")
        stateFile:close()
    end
end

hl.window_rule({
    name = "cover-screen-borderless",
    match = { tag = "cover-screen" },

    border_size = 0,
    rounding    = 0,
    decorate    = false,
    no_anim     = true,
    no_blur     = true,
    no_dim      = true,
    no_shadow   = true,
    opacity     = "1.0 override 1.0 override 1.0 override",
    opaque      = true,
})

-- Dwindle is the default layout.  A Master workspace receives a later,
-- workspace-specific normal-border override from SetActiveWorkspaceLayout.
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
    name   = "wifi-select-float",
    match  = { class = "wifi-select" },
    float  = true,
    opaque = true,
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

local function organizeWindowsOnePerWorkspace()
    local activeWindow = hl.get_active_window()
    local activeAddress = activeWindow and activeWindow.address or nil
    local activeTarget = nil
    local orderedWindows = {}
    local workspaces = hl.get_workspaces()

    table.sort(workspaces, function(a, b)
        return a.id < b.id
    end)

    -- Snapshot in workspace-major order before moving anything.  Therefore all
    -- windows originally on workspace 1 remain before all windows originally
    -- on workspace 2, independently of when those windows were created.
    for _, workspace in ipairs(workspaces) do
        if not workspace.special and workspace.id > 0 then
            local windows = hl.get_workspace_windows(workspace)

            for _, window in ipairs(windows or {}) do
                if not window.floating then
                    table.insert(orderedWindows, window)
                end
            end
        end
    end

    for target, window in ipairs(orderedWindows) do
        if window.address == activeAddress then
            activeTarget = target
        end

        if not window.workspace or window.workspace.id ~= target then
            hl.dispatch(hl.dsp.window.move({
                workspace = target,
                window = window,
            }))
        end
    end

    if activeTarget then
        hl.dispatch(hl.dsp.focus({ workspace = activeTarget }))
    end
end

function MoveWindowToWorkspace(workspace)
    local window = hl.get_active_window()
    if not window then
        return
    end

    if fullscreenRule:is_enabled() then
        for _, existingWindow in ipairs(hl.get_workspace_windows(workspace) or {}) do
            if existingWindow.address ~= window.address then
                return
            end
        end
    end

    hl.dispatch(hl.dsp.window.move({
        workspace = workspace,
        window = window,
        follow = true,
    }))
end

local function insertFullscreenWindow(window)
    if window and window.floating then
        return
    end

    if not fullscreenRule:is_enabled()
        or not window
        or not window.workspace
        or window.workspace.special
        or window.workspace.id <= 0 then
        return
    end

    local source = window.workspace.id
    local sourceWindows = hl.get_workspace_windows(source) or {}

    -- If this window opened on an empty workspace, it is already isolated.
    if #sourceWindows <= 1 then
        return
    end

    local insertion = source + 1
    local workspaces = hl.get_workspaces()

    -- Move from right to left so every later workspace is vacant before its
    -- predecessor moves into it.  This preserves the existing window order.
    table.sort(workspaces, function(a, b)
        return a.id > b.id
    end)

    for _, workspace in ipairs(workspaces) do
        if not workspace.special and workspace.id >= insertion then
            local windows = hl.get_workspace_windows(workspace) or {}

            for _, existingWindow in ipairs(windows) do
                if existingWindow.address ~= window.address then
                    hl.dispatch(hl.dsp.window.move({
                        workspace = workspace.id + 1,
                        window = existingWindow,
                        follow = false,
                    }))
                end
            end
        end
    end

    hl.dispatch(hl.dsp.window.move({
        workspace = insertion,
        window = window,
        follow = true,
    }))
end

hl.on("window.open", insertFullscreenWindow)

function ToggleFullscreenMode()
    if fullscreenRule:is_enabled() then
        fullscreenRule:set_enabled(false)
        setFullscreenModeState(false)
    else
        organizeWindowsOnePerWorkspace()
        fullscreenRule:set_enabled(true)
        setFullscreenModeState(true)
    end

    hl.exec_cmd("pkill -RTMIN+9 -x waybar")
end

function FullscreenActiveWindow()
    local window = hl.get_active_window()
    if not window then
        return
    end

    if window.fullscreen ~= 0 then
        hl.dispatch(hl.dsp.window.fullscreen({
            action       = "unset",
            mode         = "fullscreen",
            layout_aware = false,
            window       = window,
        }))
        hl.dispatch(hl.dsp.window.tag({ tag = "-cover-screen", window = window }))
        return
    end

    hl.dispatch(hl.dsp.window.float({ action = "unset", window = window }))
    hl.dispatch(hl.dsp.window.tag({ tag = "+cover-screen", window = window }))
    hl.dispatch(hl.dsp.window.fullscreen({
        action       = "set",
        mode         = "fullscreen",
        layout_aware = false,
        window       = window,
    }))
end
