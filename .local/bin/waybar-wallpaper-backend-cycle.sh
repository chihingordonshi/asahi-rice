#!/usr/bin/env bash
set -euo pipefail

# Click-to-toggle (no text entry) -- matches waybar-power-profile-cycle.sh's pattern.
current=$(awk -F' *= *' '/^backend = /{print $2}' ~/.config/waypaper/config.ini)

case "$current" in
    mpvpaper) next=sway ;;
    swaybg)   next=mpv ;;
    *)        next=sway ;;
esac

exec ~/.local/bin/waypaper-set-backend.sh "$next"
