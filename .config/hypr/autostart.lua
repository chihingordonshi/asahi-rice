
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
    -- swaybg disabled by request; leaving line commented rather than deleted
    -- since the comment block above documents why it was here.
    -- hl.exec_cmd("systemctl --user start swaybg-wallpaper.service")
    -- Silently restores the last wallpaper via whichever backend is set in
    -- ~/.config/waypaper/config.ini (swaybg or mpvpaper -- see the waybar
    -- mpv/sway menu, waypaper-set-backend.sh). --restore never opens the
    -- waypaper GUI, it just re-applies the last pick.
    hl.exec_cmd("waypaper --restore")
    -- Ports KDE Plasma's "org.cachyos.quickmenu" plasmoid (a HUD launcher stack
    -- pinned to the desktop) since this machine runs Hyprland day-to-day, not
    -- Plasma. Quickshell/QML (caelestia/noctalia) is a documented aarch64-linux
    -- engine-level dead end here (see .config/agents/fedora-asahi-setup.md), so
    -- this is a custom Python + GTK4 + Cairo + gtk4-layer-shell reimplementation
    -- instead -- ~/.local/bin/hypr-quickmenu, config at ~/.config/hypr-quickmenu/.
    hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-quickmenu")
    -- Custom Cairo-drawn digital clock (top-right, JetBrains Mono Nerd Font, cyan
    -- accent glow), pinned via gtk4-layer-shell since KDE plasmoids don't run
    -- outside the Plasma shell. LD_PRELOAD works around a known gtk4-layer-shell
    -- + Python dlopen ordering issue (layer-shell must load before libwayland-client).
    hl.exec_cmd("env LD_PRELOAD=/usr/lib64/libgtk4-layer-shell.so.0 python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/cairo-clock.py")
--    hl.exec_cmd("brave-browser --password-store=basic")
--  hl.exec_cmd(terminal)
    -- --disable notificationitem: waybar's custom/fcitx5 module already shows IME
    -- status, so fcitx5's own StatusNotifierItem tray icon is redundant. Config-file
    -- DisabledAddons= doesn't suppress it (notificationitem is an on-demand addon
    -- classicui pulls in as an optional dep; DisabledAddons in ~/.config/fcitx5/config
    -- is only checked for eager-loaded addons, confirmed via `fcitx5 -d -D` debug
    -- logs), but the --disable CLI flag does (its own separate override, logged as
    -- "Override Disabled Addons"). --replace guards against org.fcitx.Fcitx5's dbus
    -- service activation (Exec=/usr/bin/fcitx5, no flags) winning the startup race
    -- and grabbing the bus name with the tray icon still enabled.
    hl.exec_cmd("fcitx5 --disable notificationitem --replace -d")
    hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/hypr-workspace-watch")
    -- Watches ~/Videos/Wallpapers and auto-downscales anything above 1080p:
    -- Asahi's GPU has no hardware h264/hevc decode via VAAPI, so 4K clips
    -- overrun single-threaded software decode and play back in slow motion.
    hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/wallpaper-auto-downscale")
--  hl.exec_cmd("tide-island")
--  hl.exec_cmd("wayvnc")
--  hl.exec_cmd("safeeyes")            -- not packaged for Fedora, no COPR/dnf path found
--  hl.exec_cmd("warp-taskbar")        -- Warp isn't this machine's terminal, kitty is
--  hl.exec_cmd("mihomo-party")
end)
