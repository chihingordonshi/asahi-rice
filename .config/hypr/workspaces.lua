
------------------------
---- WORKSPACES ----
------------------------

local function first_empty_workspace()
    local id = 1
    while true do
        local windows = hl.get_workspace_windows(id)
        if not windows or #windows == 0 then
            return id
        end
        id = id + 1
    end
end

function GoToFirstEmptyWorkspace()
    hl.dispatch(hl.dsp.focus({ workspace = first_empty_workspace() }))
end

function MoveWindowToFirstEmptyWorkspace()
    hl.dispatch(hl.dsp.window.move({ workspace = first_empty_workspace() }))
end

local skipGapFillOnce = false

function GoToWorkspace(id)
    -- Honor populated workspaces before the first empty one. Redirect only
    -- when the requested workspace is empty, or lies after the first empty
    -- slot, so workspace 1 remains selectable while it contains windows.
    local first_empty = first_empty_workspace()
    local windows = hl.get_workspace_windows(id)
    local requested_is_empty = not windows or #windows == 0
    local target = id

    if requested_is_empty or id > first_empty then
        target = first_empty
    end

    if target ~= id then
        skipGapFillOnce = true
    end
    hl.dispatch(hl.dsp.focus({ workspace = target }))
end

hl.on("workspace.active", function(ws)
    if skipGapFillOnce then
        skipGapFillOnce = false
        return
    end

    if not ws or ws.special or ws.windows > 0 then
        return
    end

    local target = first_empty_workspace()
    if target ~= ws.id then
        hl.dispatch(hl.dsp.focus({ workspace = target }))
    end
end)
