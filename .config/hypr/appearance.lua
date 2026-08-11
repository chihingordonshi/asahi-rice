
-----------------------
---- LOOK AND FEEL ----
-----------------------

-- Refer to https://wiki.hypr.land/Configuring/Basics/Variables/
hl.config({
    general = {
        gaps_in  = 4,
        gaps_out = 6,

        border_size = 2,

        col = {
            active_border   = { colors = {"rgba(fed4ffee)", "rgba(8147e6ee)"}, angle = 45 },
            inactive_border = "rgba(00000000)",
        },

        -- Set to true to enable resizing windows by clicking and dragging on borders and gaps
        resize_on_border = false,

        -- Please see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Tearing/ before you turn this on
        allow_tearing = false,

        layout = "dwindle",
    },

    decoration = {
        rounding       = 8,
        rounding_power = 3,

        -- Change transparency of focused and unfocused windows
        active_opacity   = 0.96,
        inactive_opacity = 0.80,

        shadow = {
            enabled      = true,
            range        = 10,
            render_power = 3,
            color        = 0xee101010,
        },

        blur = {
            enabled   = true,
            size      = 2,
            passes    = 1,
            vibrancy  = 0.4,
        },

        glow = {
            enabled = true,
            range = 8,
            color = 0xff6282f5,
        }
    },

    animations = {
        enabled = true,
    },
})
