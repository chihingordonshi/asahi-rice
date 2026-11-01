#!/usr/bin/env bash
# Deploy the local theme and switch the next boot to SDDM, without stopping a session.
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
theme_source="$repo_root/setup/sddm/themes/macos"
theme_target=/usr/local/share/sddm/themes/macos

rpm -q --quiet sddm sddm-wayland-generic || {
    printf 'Install sddm and sddm-wayland-generic first.\n' >&2
    exit 1
}
test -f "$theme_source/Main.qml"
test -f /usr/share/wayland-sessions/hyprland-uwsm.desktop

while IFS= read -r -d '' file; do
    relative=${file#"$theme_source/"}
    sudo install -D -o root -g root -m 0644 "$file" "$theme_target/$relative"
done < <(find "$theme_source" -type f ! -name README.md -print0)
sudo install -D -o root -g root -m 0644 \
    "$repo_root/setup/sddm/10-macos.conf" /etc/sddm.conf.d/10-macos.conf
sudo install -D -o root -g root -m 0644 \
    "$repo_root/setup/sddm/weston.ini" /etc/sddm/weston.ini

# Select the same uwsm session as the existing Hyprland login, never autologin.
# Preserve SDDM's own remembered choice on subsequent deployments.
if ! sudo test -e /var/lib/sddm/state.conf; then
    state=$(mktemp)
    trap 'rm -f -- "$state"' EXIT
    printf '[Last]\nSession=/usr/share/wayland-sessions/hyprland-uwsm.desktop\nUser=%s\n' \
        "${SUDO_USER:-$USER}" > "$state"
    sudo install -o sddm -g sddm -m 0600 "$state" /var/lib/sddm/state.conf
fi
if command -v restorecon >/dev/null 2>&1; then
    sudo restorecon -RF "$theme_target" /etc/sddm.conf.d/10-macos.conf /etc/sddm/weston.ini /var/lib/sddm/state.conf
fi

if systemctl cat plasmalogin.service >/dev/null 2>&1; then
    sudo systemctl disable plasmalogin.service
fi
sudo systemctl enable --force sddm.service
printf 'SDDM with the macOS-inspired theme is configured for the next boot; this session was not stopped.\n'
