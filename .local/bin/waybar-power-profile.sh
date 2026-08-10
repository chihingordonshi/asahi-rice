#!/usr/bin/env bash
set -euo pipefail

profile=$(busctl --system get-property net.hadess.PowerProfiles /net/hadess/PowerProfiles \
    net.hadess.PowerProfiles ActiveProfile | cut -d'"' -f2)

case "$profile" in
    performance) icon="󰑣" ;;
    balanced)    icon="󰗑" ;;
    power-saver) icon="󰌪" ;;
    *)           icon="?" ;;
esac

printf '{"text":"%s","tooltip":"Power profile: %s\\nClick to cycle"}\n' "$icon" "$profile"
