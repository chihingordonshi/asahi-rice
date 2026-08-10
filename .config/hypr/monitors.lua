-- Monitor config. dot-files had no monitors.lua to copy (the require() target never
-- existed), so this is authored fresh — pinned to this machine's actual detected
-- hardware (via `hyprctl monitors`) rather than left on "preferred/auto" guesses.

hl.monitor({
    output   = "eDP-1",
    mode     = "2560x1600@60",
    position = "auto",
    scale    = 2,
})
