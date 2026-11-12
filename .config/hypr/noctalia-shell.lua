-- Noctalia v5 native-shell integration, separate from generated noctalia.lua.
-- https://docs.noctalia.dev/noctalia/compositor-settings/hyprland/
hl.layer_rule({
    name = "noctalia-no-anim",
    match = {
        namespace = "^noctalia-(bar-.+|notification|dock|panel|attached-panel|osd|window-switcher)$",
    },
    no_anim = true,
})

hl.window_rule({
    match = { class = "dev.noctalia.Noctalia" },
    float = true,
    size = { 1080, 920 },
})

-- Native smart mode counts floating windows too. Sample compositor objects,
-- never hyprctl/pgrep subprocesses; IPC runs only on a mode/process transition.
-- Explicit show/hide blocks pointer/edge reveal; Noctalia owns the surfaces.
local runtime = os.getenv("XDG_RUNTIME_DIR") or "/tmp"
local forceFile = runtime .. "/noctalia-bar.force-show"
local desiredFile = runtime .. "/noctalia-bar.desired"
local function shellQuote(value)
    return "'" .. value:gsub("'", "'\\''") .. "'"
end
local function pinnedOnDisk()
    local file = io.open(forceFile, "r")
    if not file then return false end
    file:close()
    return true
end

if NoctaliaBarController then NoctaliaBarController.stop() end
local controller = { active = true, pinned = pinnedOnDisk() }
NoctaliaBarController = controller

-- show_cursor=false excludes the pointer from the image, not the live selector.
-- Own this temporary compositor override only while a region overlay is mapped.
local savedCursorInvisible
local function restoreCaptureCursor()
    if savedCursorInvisible == nil then return end
    hl.config({ cursor = { invisible = savedCursorInvisible } })
    savedCursorInvisible = nil
end

local function syncCaptureCursor()
    if not controller.active then return end
    local ok, err = pcall(function()
        local selecting = false
        for _, layer in ipairs(hl.get_layers({ namespace = "noctalia-screenshot-region" })) do
            if layer.mapped then selecting = true; break end
        end
        if selecting and savedCursorInvisible == nil then
            local previous = hl.get_config("cursor.invisible")
            if type(previous) ~= "boolean" then return end
            savedCursorInvisible = previous
            if not previous then hl.config({ cursor = { invisible = true } }) end
        elseif not selecting then
            restoreCaptureCursor()
        end
    end)
    if not ok then
        restoreCaptureCursor()
        error(err)
    end
end

local function poll()
    if not controller.active then return end
    syncCaptureCursor()
    -- A hard-hidden bar may have no layer, including after a compositor reload.
    -- The enabled wallpaper provides stable discovery while that bar is hidden.
    local layers = hl.get_layers({ namespace = "noctalia-bar-default" })
    if #layers == 0 then
        layers = hl.get_layers({ namespace = "noctalia-wallpaper" })
    end
    for _, layer in ipairs(layers) do
        if layer.pid and layer.pid ~= controller.pid then
            controller.pid = layer.pid
            controller.visibility = nil -- Shell startup/restart needs a fresh sync.
            controller.reserve = nil
        end
    end
    -- Noctalia may start after Hyprland. Retain a known PID while layers vanish.
    if not controller.pid then return end
    local workspace = hl.get_active_special_workspace() or hl.get_active_workspace()
    local visibility = "show"
    if workspace and not controller.pinned then
        for _, window in ipairs(hl.get_windows({ workspace = workspace, mapped = true, floating = false })) do
            if window.mapped and not window.hidden and not window.floating then
                visibility = "hide"
                break
            end
        end
    end
    if visibility ~= controller.visibility or controller.pinned ~= controller.reserve then
        -- Publish the latest desired state atomically. The helper serializes IPC
        -- and reads this state after locking, so rapid toggles cannot apply stale
        -- reservation changes. Reapply visibility after any settings reload.
        local file = io.open(desiredFile .. ".tmp", "w")
        if not file then return end
        file:write(tostring(controller.pinned), " ", visibility, "\n")
        file:close()
        if not os.rename(desiredFile .. ".tmp", desiredFile) then return end
        hl.exec_cmd(shellQuote(os.getenv("HOME") .. "/.local/bin/noctalia-bar-apply") .. " >/dev/null")
        controller.visibility = visibility
        controller.reserve = controller.pinned
    end
end

function ToggleNoctaliaVisibility()
    if not controller.active then return end
    -- Keep manual show pinned so the next window-count poll cannot hide it.
    controller.pinned = not controller.pinned
    if controller.pinned then
        local file = io.open(forceFile, "w")
        if file then file:close() end
    else
        os.remove(forceFile)
    end
    -- Both shortcuts also force fresh visibility/reservation IPC immediately.
    controller.visibility = nil
    controller.reserve = nil
    poll()
end

function controller.stop()
    if not controller.active then return end
    controller.active = false
    if controller.timer then controller.timer:set_enabled(false) end
    if controller.unload then controller.unload:remove() end
    if controller.workspace_active then controller.workspace_active:remove() end
    if controller.special_active then controller.special_active:remove() end
    if controller.capture_opened then controller.capture_opened:remove() end
    if controller.capture_closed then controller.capture_closed:remove() end
    restoreCaptureCursor()
end

controller.capture_opened = hl.on("layer.opened", syncCaptureCursor)
controller.capture_closed = hl.on("layer.closed", syncCaptureCursor)
controller.timer = hl.timer(poll, { timeout = 200, type = "repeat" })
-- React immediately to workspace switches; the timer covers window/state changes.
controller.workspace_active = hl.on("workspace.active", poll)
controller.special_active = hl.on("workspace.special_active", poll)
controller.unload = hl.on("config.unload", controller.stop)
poll()
