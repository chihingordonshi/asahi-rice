
-- Keep single-window gaps scoped to those workspaces instead of changing the
-- compositor-wide gaps whenever focus moves between workspaces.
hl.workspace_rule({ workspace = "w[tv1]s[false]", gaps_out = 0 })

-- Keep both configured special workspaces on the sole tiled layout.
hl.workspace_rule({
    workspace = "special:magic",
    layout    = "dwindle",
})

hl.workspace_rule({
    workspace = "special:calendar",
    layout    = "dwindle",
})
