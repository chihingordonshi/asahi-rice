
-------------------
---- AUTOSTART ----
-------------------

-- See https://wiki.hypr.land/Configuring/Basics/Autostart/

-- waybar.lua owns auto-hide through a native Hyprland timer on each config
-- load. Do not also start the legacy shell controller here.

hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE XMODIFIERS")
    hl.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ 0")
    hl.exec_cmd("xrdb -merge " .. os.getenv("HOME") .. "/.Xresources")
    hl.exec_cmd("/usr/bin/kwalletd6")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd("mako")
    hl.exec_cmd("systemctl --user start waybar.service")
    hl.exec_cmd("systemctl --user start swaybg-wallpaper.service random-wallpaper.timer")
--  hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-quickmenu")
--  hl.exec_cmd("env LD_PRELOAD=/usr/lib64/libgtk4-layer-shell.so.0 python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/cairo-clock.py")
    -- Retain the candidate panel and its native Wayland input-method-v2 bridge.
    hl.exec_cmd("env -u GTK_IM_MODULE -u QT_IM_MODULE ibus-daemon --daemonize --replace --xim --restart --panel='/usr/libexec/ibus-ui-gtk3 --enable-wayland-im' --emoji-extension=disable")
    hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-workspace-watch")
end)
