#!/usr/bin/env bash
set -euo pipefail

im=$(fcitx5-remote -n)

case "$im" in
    keyboard-us) text="EN" ;;
    pinyin)      text="CN" ;;
    *)           text="$im" ;;
esac

printf '{"text":"%s","tooltip":"Input method: %s (click to switch)"}\n' "$text" "$im"
