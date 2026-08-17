#!/usr/bin/env bash
set -euo pipefail

backend=$(awk -F' *= *' '/^backend = /{print $2}' ~/.config/waypaper/config.ini)

case "$backend" in
    mpvpaper) label="mpv" ;;
    swaybg)   label="sway" ;;
    *)        label="$backend" ;;
esac

printf '{"text":"%s","tooltip":"Wallpaper backend: %s\\nClick to switch"}\n' "$label" "$label"
