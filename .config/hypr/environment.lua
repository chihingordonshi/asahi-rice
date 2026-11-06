
-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------

-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Environment-variables/

hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Bibata-Original-Classic")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
-- Native Wayland clients use the IBus input-method-v2 bridge; do not force
-- GTK_IM_MODULE or QT_IM_MODULE. XWayland clients use IBus through XIM.
hl.env("XMODIFIERS", "@im=ibus")
