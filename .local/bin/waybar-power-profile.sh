#!/usr/bin/env bash
set -euo pipefail

if ! profile=$(busctl --system get-property net.hadess.PowerProfiles /net/hadess/PowerProfiles \
    net.hadess.PowerProfiles ActiveProfile 2>/dev/null | cut -d'"' -f2); then
    # An unavailable optional service must not make the button disappear.
    printf '{"text":"󰐥","tooltip":"Power profiles unavailable\\nPower-profile service is missing or unreachable.","class":"unavailable"}\n'
    exit 0
fi

# Plain monochrome Nerd Font glyphs: rocket, scale-balance, and leaf (not emoji).
case "$profile" in
    performance) icon="󰑣" ;;
    balanced)    icon="󰗑" ;;
    power-saver) icon="󰌪" ;;
    *)           icon="󰐥" ;;
esac

printf '{"text":"%s","tooltip":"Power profile: %s\\nClick to cycle"}\n' "$icon" "$profile"
