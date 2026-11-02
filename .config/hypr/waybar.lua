-- Keep polling inside Hyprland: no processes or IPC are needed between changes.
local runtime = os.getenv("XDG_RUNTIME_DIR") or "/tmp"
local forceFile = runtime .. "/waybar-autohide.force-show"
local stateFile = runtime .. "/waybar-autohide.state"
local hoverHeight, triggerDelay, startupGrace = 72, 200, 1000

local function readFile(path)
    local file = io.open(path, "r")
    if not file then return nil end
    local contents = file:read("*a")
    file:close()
    return contents
end

-- os.clock measures CPU time, not elapsed time. /proc/uptime is monotonic and
-- reading it uses Lua's own I/O, unlike spawning date for every sample.
local function nowMs()
    local uptime = readFile("/proc/uptime")
    local seconds = uptime and tonumber(uptime:match("^[%d.]+"))
    return seconds and math.floor(seconds * 1000 + 0.5)
end

local function processStart(pid)
    local stat = readFile("/proc/" .. pid .. "/stat")
    local fields = stat and stat:match("^%d+ %(.+%) (.+)$")
    if not fields then return nil end
    local index = 0
    for field in fields:gmatch("%S+") do
        index = index + 1
        if index == 20 then return field end -- /proc/PID/stat field 22
    end
end

-- Also guard against this module being evaluated twice in the same Lua state.
-- A real config reload creates a fresh state; the small runtime file below
-- preserves visibility then, since SIGUSR1 is a toggle, not an idempotent show.
if WaybarAutohideController then WaybarAutohideController.stop() end
local controller = { active = true }
WaybarAutohideController = controller
local bars = {}
for line in (readFile(stateFile) or ""):gmatch("[^\n]+") do
    local pid, start, shown, since = line:match("^(%d+) (%d+) ([01]) (%d+)$")
    if pid then
        bars[tonumber(pid)] = {
            start = start, shown = shown == "1", since = tonumber(since),
        }
    end
end

local function persist()
    local file = io.open(stateFile, "w")
    if not file then return end
    local pids = {}
    for pid in pairs(bars) do pids[#pids + 1] = pid end
    table.sort(pids)
    for _, pid in ipairs(pids) do
        local bar = bars[pid]
        file:write(string.format("%d %s %d %d\n", pid, bar.start,
            bar.shown and 1 or 0, bar.since))
    end
    file:close()
end

local function poll()
    if not controller.active then return end
    local now = nowMs()
    if not now then return end
    local dirty, checked = false, {}

    -- Layer PIDs discover restarted/new bars without pgrep. Keep a known PID
    -- while its process lives even if hiding temporarily removes its layer.
    for _, layer in ipairs(hl.get_layers({ namespace = "waybar" })) do
        local pid = tonumber(layer.pid)
        if pid and pid > 0 and pid == math.floor(pid) and not checked[pid] then
            local start = processStart(pid)
            checked[pid] = true
            if start and (not bars[pid] or bars[pid].start ~= start) then
                bars[pid] = { start = start, shown = true, since = now }
                dirty = true
            end
        end
    end
    for pid, bar in pairs(bars) do
        if not checked[pid] and processStart(pid) ~= bar.start then
            bars[pid] = nil
            dirty = true
        end
    end

    local force = readFile(forceFile) ~= nil
    local workspace = hl.get_active_workspace()
    local empty = workspace and workspace.windows == 0
    local cursorY
    if workspace and not force and not empty then
        local cursor = hl.get_cursor_pos()
        local monitor = hl.get_monitor_at_cursor()
        if cursor and monitor then cursorY = math.floor(cursor.y - monitor.y) end
    end

    for pid, bar in pairs(bars) do
        local desired
        if now - bar.since < startupGrace then
            bar.edgeSince = nil
        elseif workspace then
            if force or empty then
                bar.edgeSince = nil
                desired = true
            elseif cursorY then
                if bar.shown and cursorY < hoverHeight then
                    bar.edgeSince = nil
                    desired = true
                elseif cursorY <= 0 then
                    bar.edgeSince = bar.edgeSince or now
                    desired = now - bar.edgeSince >= triggerDelay
                else
                    bar.edgeSince = nil
                    desired = false
                end
            else
                bar.edgeSince = nil
            end
        end
        if desired ~= nil and desired ~= bar.shown then
            -- Only visibility transitions spawn a shell; kill itself is a shell
            -- builtin. Never infer visibility from reserved space or mapped.
            hl.exec_cmd("kill -USR1 " .. pid)
            bar.shown = desired
            dirty = true
        end
    end
    if dirty then persist() end
end

function ToggleWaybarVisibility()
    if readFile(forceFile) ~= nil then
        os.remove(forceFile)
    else
        local file = io.open(forceFile, "w")
        if file then file:close() end
    end
    poll()
end

function controller.stop()
    if not controller.active then return end
    controller.active = false
    if controller.timer then controller.timer:set_enabled(false) end
    if controller.unload then controller.unload:remove() end
    persist()
end

os.remove(runtime .. "/waybar-autohide.normal-hidden")
controller.timer = hl.timer(poll, { timeout = 100, type = "repeat" })
controller.unload = hl.on("config.unload", controller.stop)
poll()
