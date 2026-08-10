
---------------
---- INPUT ----
---------------

-- kb_layout confirmed against `localectl status` for this machine (matches the real
-- config's "us" anyway). kb_options/sensitivity/touchpad behavior adopted from the real
-- input.lua since those are preference, not hardware -- the per-device hl.device() block
-- there targeted a specific XPS16 touchpad hardware ID that doesn't exist here, so it's
-- dropped rather than copied.
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
        },
    },
})

hl.gesture({
    fingers   = 3,
    direction = "horizontal",
    action    = "workspace"
})
