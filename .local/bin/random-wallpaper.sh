#!/usr/bin/env bash
set -euo pipefail

wallpaper_dir="$HOME/Pictures/Wallpapers"
runtime_dir="${XDG_RUNTIME_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}}"
state_file="$runtime_dir/swaybg-wallpaper.current"

if [[ ! -d "$wallpaper_dir" ]]; then
    printf 'Wallpaper directory does not exist: %s\n' "$wallpaper_dir" >&2
    exit 1
fi

# Recurse into collections; NUL delimiters preserve spaces and newlines in paths.
# Follow a symlinked library root, but not arbitrary symlinked subdirectories.
mapfile -d '' -t wallpapers < <(find -H "$wallpaper_dir" -type f \( \
    -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o \
    -iname '*.webp' -o -iname '*.bmp' -o -iname '*.gif' -o \
    -iname '*.tif' -o -iname '*.tiff' \) -print0)
if (( ${#wallpapers[@]} == 0 )); then
    printf 'No supported wallpaper images found in %s\n' "$wallpaper_dir" >&2
    exit 1
fi

previous=
if [[ -r "$state_file" ]]; then
    IFS= read -r -d '' previous < "$state_file" || true
fi
candidates=()
for image in "${wallpapers[@]}"; do
    [[ "$image" == "$previous" ]] || candidates+=("$image")
done
# A one-image library can still be restarted after output/session changes.
if (( ${#candidates[@]} == 0 )); then
    candidates=("${wallpapers[@]}")
fi
IFS= read -r -d '' pick < <(printf '%s\0' "${candidates[@]}" | shuf -z -n 1)
mkdir -p -- "$runtime_dir"
printf '%s\0' "$pick" > "$state_file"

# Keep swaybg in the foreground so systemd supervises and cleans it up normally.
exec swaybg -i "$pick" -m fill
