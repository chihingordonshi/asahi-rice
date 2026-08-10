#!/usr/bin/env bash
set -euo pipefail

powered=$(bluetoothctl show | awk -F': ' '/^\s*Powered:/{print $2}')

if [[ "$powered" == "yes" ]]; then
    icon="󰂯"
    state="on"
else
    icon="󰂲"
    state="off"
fi

printf '{"text":"%s","tooltip":"Bluetooth: %s (click to open settings)"}\n' "$icon" "$state"
