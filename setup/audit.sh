#!/usr/bin/env bash
set -uo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
failures=0

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    ((failures += 1))
}

while IFS= read -r relative || [[ -n "$relative" ]]; do
    [[ -z "$relative" || "$relative" == \#* ]] && continue
    source_path="$repo_root/$relative"
    target_path="$HOME/$relative"
    [[ -L "$target_path" ]] || { fail "$target_path is not a symlink"; continue; }
    [[ $(readlink -f -- "$target_path") == $(readlink -f -- "$source_path") ]] || fail "$target_path does not resolve into this clone"
done < "$repo_root/setup/home-files.txt"

while IFS= read -r package || [[ -n "$package" ]]; do
    [[ -z "$package" || "$package" == \#* ]] && continue
    rpm -q --quiet "$package" || fail "RPM missing: $package"
done < "$repo_root/setup/dnf-packages.txt"

while read -r scope app _ || [[ -n "${scope:-}" ]]; do
    [[ -z "${scope:-}" || "$scope" == \#* ]] && continue
    flatpak info --"$scope" "$app" >/dev/null 2>&1 || fail "$scope Flatpak missing: $app"
done < "$repo_root/setup/flatpak-apps.txt"

for unit in $(sed '/^\s*#/d; /^\s*$/d' "$repo_root/setup/user-services.txt"); do
    systemctl --user is-enabled --quiet "$unit" || fail "user unit not enabled: $unit"
done

for codec in h264 hevc av1 vp9 aac opus vorbis mp3 flac; do
    ffmpeg -hide_banner -decoders 2>/dev/null | grep -E "[[:space:]]${codec}[[:space:]]" >/dev/null || fail "FFmpeg decoder missing: $codec"
done
for plugin in avdec_h264 avdec_h265 avdec_aac dav1ddec vp9dec opusdec vorbisdec mpg123audiodec flacdec; do
    gst-inspect-1.0 "$plugin" >/dev/null 2>&1 || fail "GStreamer decoder missing: $plugin"
done
rpm -q --quiet cloudflare-warp || fail 'Cloudflare WARP is not installed'

tracked=$(git -C "$repo_root" ls-files)
for forbidden in '.config/gh/hosts.yml' '.config/kdeconnect/' '.config/pulse/' '.config/mihomo-party/' '.config/google-chrome/' '.config/BraveSoftware/' '.claude.json' '.histfile'; do
    grep -Fq "$forbidden" <<< "$tracked" && fail "sensitive/runtime path is tracked: $forbidden"
done

if ((failures)); then
    printf '%d audit check(s) failed.\n' "$failures" >&2
    exit 1
fi
printf 'Audit passed: links, packages, codecs, services, and exclusions are consistent.\n'
