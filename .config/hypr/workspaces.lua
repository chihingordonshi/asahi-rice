
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
    -- Keep the numbered workspace sequence compact: selecting a non-empty
    -- slot jumps to the first empty slot instead of creating a gap.
    local target = first_empty_workspace()
    skipGapFillOnce = true
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
