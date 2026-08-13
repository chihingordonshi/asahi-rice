
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
		rounding = 0,
		rounding_power = 3,
                inactive_opacity = 1.00,
                glow = {
                    enabled = false,
                }
            },
            animations = {
                enabled = false,
            },
        })
    else
        hl.config({
            general = {
                gaps_in = 2,
                gaps_out = 6,
                border_size = 2,
            },
            decoration = {
		rounding = 5,
		rounding_power = 3,
                inactive_opacity = 0.94,
                glow = {
                    enabled = true,
                }
            },
            animations = {
                enabled = true,
            },
        })
    end
    TransparencyEnabled = not TransparencyEnabled

end
