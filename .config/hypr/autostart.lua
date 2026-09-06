
-------------------
---- AUTOSTART ----
-------------------

-- See https://wiki.hypr.land/Configuring/Basics/Autostart/

-- Start on config load too, so reloading applies auto-hide immediately.  The
-- script holds a singleton lock, so this is safe when a controller is running.
hl.exec_cmd(os.getenv("HOME") .. "/.config/hypr/scripts/waybar-autohide")

hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE")
    hl.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ 0")
    hl.exec_cmd("xrdb -merge " .. os.getenv("HOME") .. "/.Xresources")
    hl.exec_cmd("/usr/bin/kwalletd6")
    hl.exec_cmd("nm-applet")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd("mako")
    hl.exec_cmd("waybar")
    hl.exec_cmd("waypaper --restore")
    hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-quickmenu")
    hl.exec_cmd("env LD_PRELOAD=/usr/lib64/libgtk4-layer-shell.so.0 python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/cairo-clock.py")
    hl.exec_cmd("fcitx5 --disable notificationitem --replace -d")
    hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-workspace-watch")
    hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/wallpaper-auto-downscale")
end)
