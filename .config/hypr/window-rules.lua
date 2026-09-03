
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

-- Enabled only while fullscreen mode is active.  New windows stay on the
-- current workspace and use covering fullscreen, not maximized mode.
local fullscreenRule = hl.window_rule({
    name  = "fullscreen",
    match = { class = ".*" },

    fullscreen_state = "2 2",
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

function IsFullscreenModeActive()
    return fullscreenRule:is_enabled()
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

-- This rule affects only the sole window on a Dwindle workspace.  The tag is
-- maintained below so the decision remains per-window and per-workspace.
hl.window_rule({
    name = "single-dwindle-transparent-border",
    match = { tag = "single-dwindle-window" },

    border_color = "rgba(00000000)",
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

function UpdateWindowAppearance()
    for _, workspace in ipairs(hl.get_workspaces()) do
        local windows = hl.get_workspace_windows(workspace)
        local transparentBorder = workspace.tiled_layout == "dwindle" and #windows == 1

        for _, window in ipairs(windows) do
            hl.dispatch(hl.dsp.window.tag({
                tag = transparentBorder
                    and "+single-dwindle-window"
                    or "-single-dwindle-window",
                window = window,
            }))
        end
    end
end

hl.on("workspace.active", UpdateWindowAppearance)
hl.on("window.open", UpdateWindowAppearance)
hl.on("window.destroy", UpdateWindowAppearance)
hl.on("window.move_to_workspace", UpdateWindowAppearance)

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
                table.insert(orderedWindows, window)
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
