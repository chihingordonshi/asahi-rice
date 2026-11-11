#!/usr/bin/env bash
# Rebuild the existing, stride-patched mpv without changing its source tree,
# downloading code, or installing system files.
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
source_dir=${1:-"$HOME/.local/src/mpv-touchbar"}
build_dir="$repo_root/.build/touchbar-mpv"

if [[ $# -gt 1 || ! -f "$source_dir/meson.build" ]]; then
    echo "Usage: $0 [path-to-patched-mpv-source]" >&2
    exit 1
fi
source_dir=$(cd -- "$source_dir" && pwd -P)
# Stock mpv corrupts this narrow panel's output. Verify the saved workaround
# is present rather than silently producing an unsuitable player.
if ! patch --dry-run --reverse --batch --silent -d "$source_dir" -p1 \
        < "$repo_root/tools/mpv-touchbar-padding.patch"; then
    echo "touchbar: source needs tools/mpv-touchbar-padding.patch applied first" >&2
    exit 1
fi

setup_options=()
[[ ! -f "$build_dir/meson-private/coredata.dat" ]] || setup_options+=(--reconfigure)
meson setup "${setup_options[@]}" "$build_dir" "$source_dir" \
    --wrap-mode=nodownload --buildtype=release -Dauto_features=disabled \
    -Ddrm=enabled -Dalsa=enabled -Dpulse=enabled -Dlibmpv=false \
    -Dgl=disabled -Dlua=disabled
meson compile -C "$build_dir" -j 4
"$build_dir/mpv" --no-config --version
printf '\nTouch Bar player rebuilt: %s\n' "$build_dir/mpv"
