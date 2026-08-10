-- Autostart. dbus-update-activation-environment + kwalletd6 fix the D-Bus/secret-service
-- issue that broke `gh` auth under Hyprland earlier (no keyring daemon was running, and
-- service-activated D-Bus names started with a stale environment). hyprpolkitagent is the
-- Hyprland-ecosystem polkit agent (found in the XPS16 package list — swapped in for the
-- generic KDE one used in an earlier draft). mako is the XPS16's actual notification
-- daemon per the same package list.

hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE")
    hl.exec_cmd("/usr/bin/kwalletd6")
    hl.exec_cmd("hyprpolkitagent")
    hl.exec_cmd("mako")
    hl.exec_cmd("nm-applet --indicator")
    hl.exec_cmd("ironbar")
end)
