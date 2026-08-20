#!/usr/bin/env bash
# Copies the N most recent images from the paired iPhone's camera roll (via
# AFC/gio -- no FUSE gvfs mount needed, see /run/user/$UID/gvfs discussion)
# into ~/Pictures/phone-share. Originals are left on the phone (copy, not
# move) since AFC delete access isn't reliable enough to risk it.
set -euo pipefail

DEST="$HOME/Pictures/phone-share"
COUNT="${1:-5}"
mkdir -p "$DEST"

UUID=$(idevice_id -l | head -1)
if [ -z "$UUID" ]; then
    echo "No iPhone detected (idevice_id -l returned nothing). Plug it in, unlock it, and trust this computer." >&2
    exit 1
fi

BASE="afc://$UUID/DCIM"

gio mount "afc://$UUID/" >/dev/null 2>&1 || true

mapfile -t ROLLS < <(gio list "$BASE" 2>/dev/null | sort -V)
if [ "${#ROLLS[@]}" -eq 0 ]; then
    echo "Couldn't list $BASE -- is the phone unlocked and on the home screen?" >&2
    exit 1
fi

ALL=()
for roll in "${ROLLS[@]}"; do
    while IFS= read -r fname; do
        case "$fname" in
            *.[Jj][Pp][Gg]|*.[Jj][Pp][Ee][Gg]|*.[Hh][Ee][Ii][Cc]|*.[Pp][Nn][Gg])
                ALL+=("$roll/$fname")
                ;;
        esac
    done < <(gio list "$BASE/$roll" 2>/dev/null)
done

if [ "${#ALL[@]}" -eq 0 ]; then
    echo "No images found under $BASE" >&2
    exit 1
fi

mapfile -t LAST < <(printf '%s\n' "${ALL[@]}" | sort -V | tail -n "$COUNT")

for item in "${LAST[@]}"; do
    echo "Copying $item"
    gio copy "$BASE/$item" "$DEST/"
done

echo "Done -- ${#LAST[@]} image(s) copied to $DEST"
