
-- Ref https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- Keep single-window gaps scoped to those workspaces instead of changing the
-- compositor-wide gaps whenever focus moves between workspaces.
hl.workspace_rule({ workspace = "w[tv1]", gaps_out = 0 })

-- "Smart gaps" / "No gaps when only"
-- hl.workspace_rule({ workspace = "f[1]",   gaps_out = 0, gaps_in = 0 })
-- hl.window_rule({
--     name  = "no-gaps-wtv1",
--     match = { float = false, workspace = "w[tv1]" },
--     border_size = 0,
--     rounding    = 0,
-- })
-- hl.window_rule({
--     name  = "no-gaps-f1",
--     match = { float = false, workspace = "f[1]" },
--     border_size = 0,
--     rounding    = 0,
-- })

-- Keep the configured special workspace on the dwindle layout.
hl.workspace_rule({
    workspace = "special:magic",
    layout    = "dwindle",
})

local workspaceLayoutRules = {}

function SetActiveWorkspaceLayout(layout)
    local workspace = hl.get_active_workspace()
    if not workspace or workspace.special then
        return
    end

    local oldRule = workspaceLayoutRules[workspace.id]
    if oldRule then
        oldRule:set_enabled(false)
    end

    workspaceLayoutRules[workspace.id] = hl.workspace_rule({
        workspace = tostring(workspace.id),
        layout = layout,
    })

    if UpdateWindowAppearance then
        UpdateWindowAppearance()
    end
end
