#!/usr/bin/env bash
# Own the Touch Bar for the booth, then give it back to Codex notifications.
set -euo pipefail

asset="$HOME/.local/share/touchbar-animations/linux-showcase.mkv"
[[ -s "$asset" ]] || { echo "Missing showcase: $asset" >&2; exit 1; }

service_was_active=0
if systemctl --user is-active --quiet codex-touchbar.service; then
    service_was_active=1
    systemctl --user stop codex-touchbar.service
fi

restore() {
    if (( service_was_active )); then
        systemctl --user start codex-touchbar.service
    fi
}
trap restore EXIT

touchbar play linux-showcase --loop
