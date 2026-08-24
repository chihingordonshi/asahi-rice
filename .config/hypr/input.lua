
---------------
---- INPUT ----
---------------

hl.config({
    input = {
        kb_layout  = "us",
        kb_variant = "",
        kb_model   = "",
        kb_options = "caps:super",
        kb_rules   = "",

        follow_mouse = 1,

        sensitivity = 0.2,

        touchpad = {
            natural_scroll        = true,
            disable_while_typing  = true,
            tap_to_click          = false,
            clickfinger_behavior  = true,
        },
    },
})

hl.gesture({
    fingers   = 3,
    direction = "horizontal",
    action    = "workspace"
})

hl.gesture({
    fingers   = 3,
    direction = "up",
    action    = function()
        hl.dispatch(hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-overview"))
    end
})

hl.gesture({
    fingers   = 3,
    direction = "down",
    action    = function()
        hl.dispatch(hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-overview --dismiss"))
    end
})
