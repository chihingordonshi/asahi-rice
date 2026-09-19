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

for asset in codex-train.mkv codex-vines.mkv; do
    asset_path="$HOME/.local/share/touchbar-animations/$asset"
    probe=$(ffprobe -v error -select_streams v:0 \
        -show_entries stream=codec_name,width,height,pix_fmt,r_frame_rate \
        -of csv=p=0 "$asset_path" 2>/dev/null) || { fail "Touch Bar asset is unreadable: $asset"; continue; }
    [[ "$probe" == "ffv1,2008,60,yuv420p,30/1" ]] || fail "Touch Bar asset has unexpected video format: $asset ($probe)"
    duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$asset_path" 2>/dev/null)
    awk -v duration="$duration" 'BEGIN { exit !(duration >= 3.49 && duration <= 3.51) }' || fail "Touch Bar asset has unexpected duration: $asset ($duration)"
    [[ -z $(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$asset_path" 2>/dev/null) ]] || fail "Touch Bar asset unexpectedly contains audio: $asset"
done

/usr/bin/python3 -c 'import ast, pathlib, sys; [ast.parse(pathlib.Path(path).read_text()) for path in sys.argv[1:]]' \
    "$repo_root/tools/generate-codex-touchbar-animations.py" \
    "$repo_root/.local/bin/codex-touchbar-notify" \
    "$repo_root/.local/bin/codex-touchbar-daemon" || fail 'Codex Touch Bar Python syntax check failed'
/usr/bin/python3 "$repo_root/tests/test_codex_touchbar.py" || fail 'Codex Touch Bar behavior tests failed'
/usr/bin/sudo -n /usr/bin/systemctl start tiny-dfr >/dev/null 2>&1 || fail 'noninteractive tiny-dfr start permission is unavailable'

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
