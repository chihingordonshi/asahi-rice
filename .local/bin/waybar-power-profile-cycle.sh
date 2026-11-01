#!/usr/bin/env bash
set -euo pipefail

if ! current=$(busctl --system get-property net.hadess.PowerProfiles /net/hadess/PowerProfiles \
    net.hadess.PowerProfiles ActiveProfile 2>/dev/null | cut -d'"' -f2); then
    printf 'Power profiles unavailable: power-profile service is missing or unreachable.\n' >&2
    exit 1
fi

case "$current" in
    performance) next="balanced" ;;
    balanced)    next="power-saver" ;;
    power-saver) next="performance" ;;
    *)           next="balanced" ;;
esac

busctl --system set-property net.hadess.PowerProfiles /net/hadess/PowerProfiles \
    net.hadess.PowerProfiles ActiveProfile s "$next"

# mpvpaper (video wallpaper) burns noticeably more power than static swaybg,
# so force a one-time push to swaybg whenever we enter power-saver.
if [[ "$next" == "power-saver" ]]; then
    ~/.local/bin/waypaper-set-backend.sh sway
fi
