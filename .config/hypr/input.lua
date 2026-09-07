
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
    action    = "workspace",
})

hl.gesture({
    fingers   = 3,
    direction = "up",
    action    = function()
        hl.dispatch(hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-overview"))
    end,
})

hl.gesture({
    fingers   = 3,
    direction = "down",
    action    = function()
        hl.dispatch(hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-overview --dismiss"))
    end,
})

hl.gesture({
    fingers   = 3,
    direction = "pinch",
    action    = function()
        hl.dispatch(hl.dsp.exec_cmd(
            "pgrep -x rofi >/dev/null && pkill -x rofi || rofi -show drun"
        ))
    end,
})

-- mpv does not consume Wayland pointer-pinch events itself. Hyprland does, so
-- forward a throttled, continuous two-finger pinch to mpv's local IPC socket.
-- Ordinary two-finger scrolling remains an mpv input event and pans the video.
local mpv_pinch = {
    active     = false,
    last_scale = 0,
    pending    = 0,
}

local function flush_mpv_pinch()
    if not mpv_pinch.active or math.abs(mpv_pinch.pending) < 0.015 then
        return
    end

    local amount = math.max(-0.12, math.min(0.12, mpv_pinch.pending * 1.5))
    mpv_pinch.pending = 0
    hl.dispatch(hl.dsp.exec_cmd(string.format(
        "%s/.local/bin/mpv-gesture zoom %+.4f",
        os.getenv("HOME"),
        amount
    )))
end

local mpv_pinch_gesture = {
    fingers   = 2,
    direction = "pinch",
    action    = {
        start = function(event)
            local window = hl.get_active_window()
            mpv_pinch.active = window ~= nil
                and (window.class == "mpv" or window.initial_class == "mpv")
            mpv_pinch.last_scale = event.scale or 0
            mpv_pinch.pending = 0
        end,
        update = function(event)
            if not mpv_pinch.active then
                return
            end

            local scale = event.scale or mpv_pinch.last_scale
            mpv_pinch.pending = mpv_pinch.pending + scale - mpv_pinch.last_scale
            mpv_pinch.last_scale = scale
            flush_mpv_pinch()
        end,
        finish = function()
            flush_mpv_pinch()
            mpv_pinch.active = false
            mpv_pinch.pending = 0
        end,
    },
}

-- Only claim the global pinch gesture while mpv is focused. Browsers and other
-- native Wayland clients continue receiving their own pinch gestures otherwise.
local mpv_pinch_gesture_enabled = false

local function mpv_is_focused()
    local window = hl.get_active_window()
    return window ~= nil
        and (window.class == "mpv" or window.initial_class == "mpv")
end

local function update_mpv_pinch_gesture()
    local should_enable = mpv_is_focused()
    if should_enable and not mpv_pinch_gesture_enabled then
        hl.gesture(mpv_pinch_gesture)
        mpv_pinch_gesture_enabled = true
    elseif not should_enable and mpv_pinch_gesture_enabled then
        hl.gesture({
            fingers   = 2,
            direction = "pinch",
            action    = "unset",
        })
        mpv_pinch_gesture_enabled = false
    end
end

hl.on("window.active", update_mpv_pinch_gesture)
update_mpv_pinch_gesture()
