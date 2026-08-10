
----------------
----  MISC  ----
----------------

hl.config({
    misc = {
        force_default_wallpaper = 0,    -- Set to 0 or 1 to disable the anime mascot wallpapers
        disable_hyprland_logo   = false, -- If true disables the random hyprland logo / anime girl background. :(
    },

    -- Non-DPI-aware apps under XWayland (WeChat, WPS, ...) get an X11
    -- screen sized to the pre-scale logical resolution and then upscaled,
    -- which is what makes them blurry at scale = 1.6. This makes XWayland
    -- render at the real physical resolution instead.
    xwayland = {
        force_zero_scaling = true,
    },
})
