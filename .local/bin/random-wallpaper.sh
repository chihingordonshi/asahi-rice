#!/usr/bin/env bash
set -euo pipefail

WALLPAPER_DIR="$HOME/Pictures/Wallpapers"

mapfile -t wallpapers < <(find "$WALLPAPER_DIR" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \))
[[ ${#wallpapers[@]} -gt 0 ]] || exit 0

pick="${wallpapers[RANDOM % ${#wallpapers[@]}]}"

# swaybg has no IPC to swap its image live. It's launched as its own
# transient systemd scope (via systemd-run) so it survives after this
# oneshot service's cgroup is torn down between timer runs -- backgrounding
# it with plain `&` inside a Type=oneshot service does NOT protect it, the
# whole cgroup gets killed when the service exits. pkill also covers the
# flat-color swaybg that autostart.lua launches directly at boot, before
# the first timer tick.
pkill -x swaybg 2>/dev/null || true
systemctl --user stop swaybg-wallpaper.service 2>/dev/null || true
systemd-run --user --collect --unit=swaybg-wallpaper -- swaybg -i "$pick" -m fill
