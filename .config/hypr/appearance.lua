
-----------------------
---- LOOK AND FEEL ----
-----------------------

-- Refer to https://wiki.hypr.land/Configuring/Basics/Variables/
hl.config({
    general = {
        gaps_in  = 2,
        gaps_out = 6,

        border_size = 2,

        col = {
            active_border   = { colors = {"rgba(fed4ff86)", "rgba(8147e686)"}, angle = 45 },
            inactive_border = "rgba(00000000)",
        },

        -- Set to true to enable resizing windows by clicking and dragging on borders and gaps
        resize_on_border = false,

        -- Please see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Tearing/ before you turn this on
        allow_tearing = false,

        layout = "dwindle",
    },

    decoration = {
        rounding       = 5,
        rounding_power = 3,

        -- Change transparency of focused and unfocused windows
        active_opacity   = 1.00,
        inactive_opacity = 0.94,

        shadow = {
            enabled      = true,
            range        = 4,
            render_power = 1,
            color        = 0xee101010,
        },

        blur = {
            enabled   = true,
            size      = 4,
            passes    = 3,
            vibrancy  = 0.9,
        },

        glow = {
            enabled = true,
            range = 4,
            color = 0xff6282f5,
        }
    },

    animations = {
        enabled = true,
    },
})
