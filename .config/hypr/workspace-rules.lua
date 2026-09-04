
-- Keep single-window gaps scoped to those workspaces instead of changing the
-- compositor-wide gaps whenever focus moves between workspaces.
hl.workspace_rule({ workspace = "w[tv1]s[false]", gaps_out = 0 })

-- Keep the configured special workspace on the dwindle layout.
local magicDwindleRule = hl.workspace_rule({
    workspace = "special:magic",
    layout    = "dwindle",
})

local function enforceMagicDwindle(workspace)
    if not workspace
        or workspace.name ~= "special:magic"
        or workspace.tiled_layout == "dwindle" then
        return
    end

    -- Reapply the exact workspace rule if another runtime action ever changes
    -- the special workspace's layout.
    magicDwindleRule:set_enabled(false)
    magicDwindleRule:set_enabled(true)
end

hl.on("workspace.active", enforceMagicDwindle)

local workspaceLayoutRules = {}
local workspaceMasterBorderRules = {}
local normalActiveBorder = {
    colors = {"rgba(fed4ff86)", "rgba(8147e686)"},
    angle = 45,
}

function SetActiveWorkspaceLayout(layout)
    local workspace = hl.get_active_workspace()
    if not workspace then
        return
    end

    if workspace.special then
        enforceMagicDwindle(workspace)
        return
    end

    local oldRule = workspaceLayoutRules[workspace.id]
    if oldRule then
        oldRule:set_enabled(false)
    end

    local oldBorderRule = workspaceMasterBorderRules[workspace.id]
    if oldBorderRule then
        oldBorderRule:set_enabled(false)
        workspaceMasterBorderRules[workspace.id] = nil
    end

    workspaceLayoutRules[workspace.id] = hl.workspace_rule({
        workspace = tostring(workspace.id),
        layout = layout,
    })

    if layout == "master" then
        workspaceMasterBorderRules[workspace.id] = hl.window_rule({
            name = "master-normal-border-" .. workspace.id,
            match = { workspace = tostring(workspace.id) },
            border_color = normalActiveBorder,
        })
    end
end
