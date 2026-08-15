
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

-- Keep workspaces gap-free: landing on an empty workspace (SUPER+[num],
-- scroll, etc.) redirects to the first empty one instead. E.g. with 1,2,3
-- occupied, jumping to 5 lands on 4, not 5.
hl.on("workspace.active", function(ws)
    if not ws or ws.special or ws.windows > 0 then
        return
    end

    local target = first_empty_workspace()
    if target ~= ws.id then
        hl.dispatch(hl.dsp.focus({ workspace = target }))
    end
end)

-- Closing the last window on the last (highest-numbered) occupied workspace
-- would otherwise strand focus on that now-empty workspace. Jump back to
-- whatever is now the highest-numbered workspace that still has a window.
hl.on("window.close", function(win)
    local ws = win and win.workspace
    if not ws or ws.special then
        return
    end
    local ws_id = ws.id

    -- Deferred: at "window.close" time the window hasn't actually been
    -- removed yet, so workspace window counts aren't updated. Check again
    -- shortly after the close has actually gone through.
    hl.timer(function()
        local current = hl.get_active_workspace()
        if not current or current.id ~= ws_id or current.windows > 0 then
            return -- user moved on already, or the workspace isn't actually empty
        end

        local target = nil
        for _, other in ipairs(hl.get_workspaces()) do
            if other.windows > 0 and not other.special then
                if other.id > ws_id then
                    return -- ws_id wasn't the last occupied workspace; leave it alone
                end
                if not target or other.id > target.id then
                    target = other
                end
            end
        end

        if target then
            hl.dispatch(hl.dsp.focus({ workspace = target.id }))
        end
    end, { timeout = 50, type = "oneshot" })
end)
