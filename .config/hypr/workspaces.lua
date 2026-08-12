
------------------------
---- WORKSPACES ----
------------------------

-- keybindings.lua binds SUPER+G / SUPER+SHIFT+G to these as global function
-- references (same pattern as monitors.lua's resize_monitor). The target
-- workspace depends on runtime state, so it has to be a function evaluated
-- at keypress time, not a static hl.dsp.* dispatcher built once at bind time.

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
    -- window.move without an explicit window= targets the focused window,
    -- and (like the SUPER+SHIFT+[0-9] binds below) follows focus to the
    -- destination workspace as a side effect -- exactly "move window and
    -- follow me there".
    hl.dispatch(hl.dsp.window.move({ workspace = first_empty_workspace() }))
end
