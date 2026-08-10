
-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------

-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Environment-variables/

-- Cursor: Bibata isn't packaged for Fedora/no COPR found, so it's installed
-- manually as an XCursor theme in ~/.local/share/icons (from the GitHub
-- release tarball, not hyprcursor format -- Hyprland falls back to XCursor
-- fine via these env vars).
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Bibata-Original-Classic")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")

-- fcitx5 IM env vars, same reasoning as the real config: GTK_IM_MODULE is
-- deliberately left unset so native Wayland GTK apps keep using the
-- text-input-protocol IME path; only XWayland/Qt clients need the classic XIM vars.
hl.env("XMODIFIERS", "@im=fcitx")
hl.env("QT_IM_MODULE", "fcitx")
