#!/usr/bin/env bash
# Apply the small English/Rime profile to the current user's D-Bus session.
set -euo pipefail

gsettings set org.freedesktop.ibus.general preload-engines "['xkb:us::eng', 'rime']"
gsettings set org.freedesktop.ibus.general engines-order "['xkb:us::eng', 'rime']"
gsettings set org.freedesktop.ibus.general use-global-engine true
gsettings set org.freedesktop.ibus.general use-system-keyboard-layout true
gsettings set org.freedesktop.ibus.general embed-preedit-text false

# Hyprland owns Super+R. Do not steal Super+Space or add a second language switch.
for key in trigger triggers next-engine next-engine-in-menu prev-engine previous-engine \
           enable-unconditional disable-unconditional; do
    gsettings set org.freedesktop.ibus.general.hotkey "$key" '[]'
done

# Keep the candidate popup, not a second tray icon or a floating property toolbar.
gsettings set org.freedesktop.ibus.panel show 0
gsettings set org.freedesktop.ibus.panel show-icon-on-systray false
gsettings set org.freedesktop.ibus.panel show-im-name false
gsettings set org.freedesktop.ibus.panel lookup-table-orientation 0
for key in hotkey unicode-hotkey; do
    gsettings set org.freedesktop.ibus.panel.emoji "$key" '[]'
done
gsettings set org.freedesktop.ibus.panel.emoji load-emoji-at-startup false
