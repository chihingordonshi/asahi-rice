#!/usr/bin/env bash
set -euo pipefail

# Serialize rapid clicks so power-profile changes cannot overlap.
lock_dir=${XDG_RUNTIME_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}}
mkdir -p -- "$lock_dir"
exec 9>"$lock_dir/waybar-power-profile.lock"
flock 9

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
