
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
            disable_while_typing  = false,
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

-- While the overview is open, swipe down closes it (see --dismiss handling
-- in hypr-overview's do_command_line). Harmless no-op if the overview isn't
-- currently open.
hl.gesture({
    fingers   = 3,
    direction = "down",
    action    = function()
        hl.dispatch(hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-overview --dismiss"))
    end
})
