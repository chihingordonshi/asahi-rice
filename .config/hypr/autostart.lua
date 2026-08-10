
-------------------
---- AUTOSTART ----
-------------------

-- See https://wiki.hypr.land/Configuring/Basics/Autostart/

-- Adapted from the real config: caelestia -> waybar (Quickshell/caelestia isn't viable
-- on aarch64 here, see .config/agents/fedora-asahi-setup.md; ironbar was the first pick,
-- switched to waybar afterward), safeeyes/warp-taskbar/tide-island/wayvnc left out (not
-- installed / not part of this machine's stack).
-- kwalletd6 + dbus-update-activation-environment + swaybg are M1-specific additions not
-- present in the real config -- they fix issues unique to this machine (the gh/keyring
-- breakage under a plain, non-UWSM Hyprland launch, and the lack of a caelestia-provided
-- wallpaper/notification layer).

hl.on("hyprland.start", function ()
    hl.exec_cmd("dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE")
    hl.exec_cmd("/usr/bin/kwalletd6")
    hl.exec_cmd("nm-applet")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd("mako")
    hl.exec_cmd("waybar")
    hl.exec_cmd("systemctl --user start swaybg-wallpaper.service")
--  hl.exec_cmd("google-chrome-stable")
    hl.exec_cmd(terminal)
    hl.exec_cmd("fcitx5")
--  hl.exec_cmd("tide-island")
--  hl.exec_cmd("wayvnc")
--  hl.exec_cmd("safeeyes")            -- not packaged for Fedora, no COPR/dnf path found
--  hl.exec_cmd("warp-taskbar")        -- Warp isn't this machine's terminal, kitty is
--  hl.exec_cmd("mihomo-party")
end)
