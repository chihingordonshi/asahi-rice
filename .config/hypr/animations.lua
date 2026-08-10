-- Animations. Left on Hyprland's built-in default curves/timings rather than the custom
-- bezier set from the upstream example — this machine prioritizes reliability over rice,
-- and the defaults are already tuned reasonably.

hl.config({
    animations = {
        enabled = true,
    },
})
