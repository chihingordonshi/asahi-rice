
-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------

-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Environment-variables/

-- Cursor: Bibata-Original-Ice (the real config's choice) isn't packaged for Fedora
-- and has no COPR/dnf path found -- staying on Adwaita (installed, already verified
-- working) until that's sorted out.
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Adwaita")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")

-- fcitx5 IM env vars, same reasoning as the real config: GTK_IM_MODULE is
-- deliberately left unset so native Wayland GTK apps keep using the
-- text-input-protocol IME path; only XWayland/Qt clients need the classic XIM vars.
hl.env("XMODIFIERS", "@im=fcitx")
hl.env("QT_IM_MODULE", "fcitx")
