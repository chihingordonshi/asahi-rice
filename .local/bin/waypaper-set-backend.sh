#!/usr/bin/env bash
set -euo pipefail

# Switches waypaper's backend + wallpaper folder together, since the two are
# coupled on this machine: swaybg serves static images from ~/Pictures/Wallpapers,
# mpvpaper serves looping videos from ~/Videos/Wallpapers. Called from the waybar
# click-to-toggle (waybar-wallpaper-backend-cycle.sh). random-wallpaper.service
# (every 20min) doesn't call this -- it just calls `waypaper --random`, which
# reads whatever backend/folder is set here.

choice="${1:?usage: waypaper-set-backend.sh mpv|sway}"
CONFIG="$HOME/.config/waypaper/config.ini"

case "$choice" in
    mpv)  backend=mpvpaper; folder='~/Videos/Wallpapers' ;;
    sway) backend=swaybg;   folder='~/Pictures/Wallpapers' ;;
    *) echo "usage: waypaper-set-backend.sh mpv|sway" >&2; exit 1 ;;
esac

sed -i \
    -e "s|^backend = .*|backend = $backend|" \
    -e "s|^folder = .*|folder = $folder|" \
    "$CONFIG"

# waypaper only ever cleans up its *own* backend's old process (see
# waypaper/changer.py); it never kills a different backend's leftover process.
# Without this, switching mpv -> sway would leave mpvpaper decoding a video
# nobody sees, burning CPU/power for nothing.
pkill -x swaybg 2>/dev/null || true
pkill -x mpvpaper 2>/dev/null || true

waypaper --random

# custom/wallpaper-backend in waybar has no "interval" (signal-driven only, to
# avoid polling every N seconds just to display a value that changes on click)
# so it needs a nudge to redraw right away.
pkill -RTMIN+8 waybar 2>/dev/null || true
