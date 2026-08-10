
local TransparencyEnabled = true

function NoTransparency()
    if TransparencyEnabled then
        hl.config({
            general = {
                gaps_in = 0,
                gaps_out = 0,
                border_size = 0,
            },
            decoration = {
                active_opacity   = 1.0,
                inactive_opacity = 1.0,
                glow = {
                    enabled = false,
                }
            },
            animations = {
                enabled = false,
            },
        })
        hl.exec_cmd("quickshell ipc --any-display -p /usr/share/tide-island call island hide")
    else
        hl.config({
            general = {
                gaps_in = 8,
                gaps_out = 10,
                border_size = 2,
            },
            decoration = {
                active_opacity   = 0.96,
                inactive_opacity = 0.80,
                glow = {
                    enabled = true,
                }
            },
            animations = {
                enabled = true,
            },
        })
        hl.exec_cmd("quickshell ipc --any-display -p /usr/share/tide-island call island reveal")
    end
    TransparencyEnabled = not TransparencyEnabled

end
