#!/usr/bin/env bash
set -euo pipefail

WALLPAPER_DIR="$HOME/Pictures/Wallpapers"

mapfile -t wallpapers < <(find "$WALLPAPER_DIR" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \))
[[ ${#wallpapers[@]} -gt 0 ]] || exit 0

pick="${wallpapers[RANDOM % ${#wallpapers[@]}]}"

# Runs as the foreground process of swaybg-wallpaper.service (Restart=always),
# so systemd tracks swaybg's own PID directly and respawns it -- with a fresh
# random pick -- any time it dies, including when the compositor destroys its
# output out from under it (observed once after a hypridle restart glitch,
# not just at boot or on a rotation timer tick).
exec swaybg -i "$pick" -m fill
