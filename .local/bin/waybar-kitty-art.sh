#!/usr/bin/env bash

# Build a Mondrian-like composition from real, usable Kitty terminals.
# Left-clicking the Waybar module calls "spawn"; right-clicking calls "close".

set -uo pipefail

readonly art_class="abstract-kitty"

runtime_dir="${XDG_RUNTIME_DIR:-/tmp}"
exec 9>"$runtime_dir/waybar-kitty-art.lock"
flock -n 9 || exit 0

notify_error() {
    command -v notify-send >/dev/null 2>&1 &&
        notify-send -u normal "Kitty composition" "$1"
    printf 'waybar-kitty-art: %s\n' "$1" >&2
}

art_addresses() {
    hyprctl -j clients 2>/dev/null |
        jq -r --arg class "$art_class" \
            '.[] | select(.class == $class or .initialClass == $class) | .address'
}

close_window() {
    local address=$1
    local still_open
    local attempt

    hyprctl eval \
        "local w = hl.get_window(\"address:$address\"); if w then hl.dispatch(hl.dsp.focus({ window = w })); hl.dispatch(hl.dsp.window.close()) end" \
        >/dev/null 2>&1 || true

    # Focus and close are queued by the compositor. Wait for this target before
    # focusing the next one, otherwise a rapid cleanup can close the wrong active
    # window or leave most of the requested set untouched.
    for ((attempt = 0; attempt < 40; attempt++)); do
        still_open=$(hyprctl -j clients 2>/dev/null |
            jq -r --arg address "$address" 'any(.[]; .address == $address)')
        [[ "$still_open" == "false" ]] && return
        sleep 0.025
    done
}

close_art() {
    local address

    while IFS= read -r address; do
        [[ -n "$address" ]] || continue
        close_window "$address"
    done < <(art_addresses)
}

wait_for_window() {
    local title=$1
    local address=""
    local attempt

    for ((attempt = 0; attempt < 50; attempt++)); do
        address=$(hyprctl -j clients 2>/dev/null |
            jq -r --arg title "$title" \
                'first(.[] | select(.title == $title)) | .address // empty')
        [[ -n "$address" ]] && break
        sleep 0.04
    done

    printf '%s\n' "$address"
}

focus_window() {
    local address=$1

    hyprctl eval \
        "local w = hl.get_window(\"address:$address\"); if w then hl.dispatch(hl.dsp.focus({ window = w })) end" \
        >/dev/null 2>&1 || true
}

layout_message() {
    local message=$1

    hyprctl eval "hl.dispatch(hl.dsp.layout(\"$message\"))" \
        >/dev/null 2>&1 || true
}

window_area() {
    local address=$1

    hyprctl -j clients 2>/dev/null |
        jq -r --arg address "$address" \
            'first(.[] | select(.address == $address)) | ((.size[0] * .size[1]) // 0)'
}

random_between() {
    local lower=$1
    local upper=$2
    local span=$((upper - lower + 1))
    local random_value=$(((RANDOM << 15) | RANDOM))

    if ((span <= 1)); then
        printf '%s\n' "$lower"
    else
        printf '%s\n' "$((lower + random_value % span))"
    fi
}

format_basis_points() {
    local basis_points=$1
    local sign=""

    if ((basis_points < 0)); then
        sign='-'
        basis_points=$((-basis_points))
    fi
    printf '%s%d.%04d\n' "$sign" "$((basis_points / 10000))" "$((basis_points % 10000))"
}

# Move the focused tile toward a requested area by probing which direction a
# split-ratio delta moves that particular side of the dwindle node. Measuring
# after every nudge keeps this independent of whether the tile is left/right or
# top/bottom in its parent.
nudge_tile_to_area() {
    local address=$1
    local desired_area=$2
    local tolerance=$3
    local before after before_error after_error step reverse_step
    local attempt

    for ((attempt = 0; attempt < 8; attempt++)); do
        before=$(window_area "$address")
        ((before > 0)) || return

        before_error=$((before - desired_area))
        ((before_error < 0)) && before_error=$((-before_error))
        ((before_error <= tolerance)) && return

        if ((before_error > desired_area / 4)); then
            step='0.08'
            reverse_step='-0.16'
        else
            step='0.04'
            reverse_step='-0.08'
        fi

        focus_window "$address"
        layout_message "splitratio $step"
        after=$(window_area "$address")
        ((after > 0 && after != before)) || return

        after_error=$((after - desired_area))
        ((after_error < 0)) && after_error=$((-after_error))

        # The positive delta moved this side away from the target. Reverse the
        # probe and take an equally sized step in the useful direction.
        if ((after_error > before_error)); then
            layout_message "splitratio $reverse_step"
        fi
    done
}

action=${1:-spawn}
case "$action" in
    close)
        close_art
        exit 0
        ;;
    spawn)
        ;;
    *)
        notify_error "Usage: ${0##*/} [spawn|close]"
        exit 2
        ;;
esac

for dependency in hyprctl jq kitty flock; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        notify_error "Missing dependency: $dependency"
        exit 1
    fi
done

monitor=$(hyprctl -j monitors 2>/dev/null |
    jq -c 'first(.[] | select(.focused == true)) // first(.[])')
if [[ -z "$monitor" || "$monitor" == "null" ]]; then
    notify_error "Could not find the focused monitor"
    exit 1
fi

monitor_width=$(jq -r '(.width / (.scale // 1)) | floor' <<<"$monitor")
monitor_height=$(jq -r '(.height / (.scale // 1)) | floor' <<<"$monitor")
screen_area=$((monitor_width * monitor_height))
min_area=$((screen_area / 25))
max_area=$((screen_area / 4))
tolerance=$((screen_area / 500))

# Guard the active workspace: an empty tiled canvas creates art, a normal
# workspace with one through seven tiled clients is left completely alone, and
# a crowded workspace with eight or more tiled clients is cleaned without
# spawning replacements. Floating clients are intentionally excluded.
active_workspace=$(hyprctl -j activeworkspace 2>/dev/null | jq -r '.id')
mapfile -t existing_tiled < <(
    hyprctl -j clients 2>/dev/null |
        jq -r --argjson workspace "$active_workspace" '
            .[]
            | select(.workspace.id == $workspace and .floating == false)
            | .address'
)
if ((${#existing_tiled[@]} >= 8)); then
    for address in "${existing_tiled[@]}"; do
        close_window "$address"
    done
    exit 0
elif ((${#existing_tiled[@]} > 0)); then
    exit 0
fi

# The active tiled canvas is empty. Preserve a focused floating window, remove
# any older composition on another workspace, then build the new one here.
old_focus=$(hyprctl -j activewindow 2>/dev/null |
    jq -r --arg class "$art_class" \
        'select(.class != $class and .initialClass != $class) | .address // empty')
close_art

target_count=$((10 + RANDOM % 11))

# Low-chroma shades derived from Rosé Pine Moon's six accents. Each family
# moves only a few values at a time, giving neighboring blocks quieter color
# variation while the inherited ANSI palette remains the canonical theme.
backgrounds=(
    '#3b2c3d' '#44303f' '#4d3445'
    '#443a31' '#4d4034' '#58483a'
    '#463436' '#503a3c' '#594144'
    '#263b48' '#2b4351' '#304b5b'
    '#34474d' '#3a5057' '#415a62'
    '#3c354d' '#443b58' '#4c4263'
    '#2a273f' '#393552'
)
accents=(
    '#eb6f92' '#eb6f92' '#dc7cb8'
    '#f6c177' '#f6c177' '#f9d1a3'
    '#ea9a97' '#ea9a97' '#d9b2bb'
    '#3e8fb0' '#3e8fb0' '#58b0cc'
    '#9ccfd8' '#9ccfd8' '#a5cada'
    '#c4a7e7' '#c4a7e7' '#c6acec'
    '#908caa' '#c4a7e7'
)

run_id="${BASHPID}-${RANDOM}"
palette_offset=$((RANDOM % ${#backgrounds[@]}))
declare -a tile_addresses=()

for ((index = 0; index < target_count; index++)); do
    parent_area=$screen_area

    # Pick among the three largest tiles that can be split without either child
    # crossing the 1/25-screen minimum. This avoids the repetitive "split the
    # newest leaf" BSP look while preserving enough area for all remaining tiles.
    if ((${#tile_addresses[@]} > 0)); then
        mapfile -t candidates < <(
            hyprctl -j clients 2>/dev/null |
                jq -r --arg class "$art_class" --argjson minimum "$((2 * min_area))" '
                    [.[]
                        | select(.class == $class or .initialClass == $class)
                        | . + {area: (.size[0] * .size[1])}
                        | select(.area >= $minimum)]
                    | sort_by(-.area)
                    | .[0:3][]
                    | .address'
        )
        if ((${#candidates[@]} == 0)); then
            mapfile -t candidates < <(
                hyprctl -j clients 2>/dev/null |
                    jq -r --arg class "$art_class" '
                        [.[]
                            | select(.class == $class or .initialClass == $class)
                            | . + {area: (.size[0] * .size[1])}]
                        | sort_by(-.area)
                        | first
                        | .address // empty'
            )
        fi

        target=${candidates[RANDOM % ${#candidates[@]}]}
        parent_area=$(window_area "$target")
        focus_window "$target"
        if ((RANDOM % 2)); then
            layout_message 'togglesplit'
        fi
    fi

    color_index=$(((palette_offset + index * 7) % ${#backgrounds[@]}))
    title="abstract-kitty-${run_id}-${index}"

    kitty --detach \
        --class "$art_class" \
        --title "$title" \
        -o "background=${backgrounds[color_index]}" \
        -o 'foreground=#e0def4' \
        -o "cursor=${accents[color_index]}" \
        -o "selection_background=${accents[color_index]}" \
        -o 'selection_foreground=#232136' \
        -o 'background_opacity=1.0' \
        -o 'window_padding_width=8' \
        -o 'hide_window_decorations=yes' \
        -o 'confirm_os_window_close=0' \
        -o 'shell_integration=enabled no-title' 9>&- >/dev/null 2>&1

    address=$(wait_for_window "$title")
    if [[ -z "$address" ]]; then
        notify_error "A Kitty tile did not appear in time"
        continue
    fi

    # The rule below tiles these immediately. This fallback also makes the
    # launcher correct if Waybar is reloaded before Hyprland's config is.
    floating=$(hyprctl -j clients 2>/dev/null |
        jq -r --arg address "$address" \
            'first(.[] | select(.address == $address)) | .floating // false')
    if [[ "$floating" == "true" ]]; then
        hyprctl eval \
            "local w = hl.get_window(\"address:$address\"); if w then hl.dispatch(hl.dsp.focus({ window = w })); hl.dispatch(hl.dsp.window.float({ action = \"toggle\" })) end" \
            >/dev/null 2>&1 || true
    fi

    tile_addresses+=("$address")

    if ((index == 0)); then
        # Give the art its own root branch. Ten tiles receive about 80% of the
        # monitor; twenty receive about 90%, which makes the 4% minimum feasible.
        focus_window "$address"
        layout_message 'movetoroot'
        art_share_percent=$((70 + target_count))
        before_area=$(window_area "$address")
        share_delta=$(format_basis_points "$(((art_share_percent - 50) * 100))")
        layout_message "splitratio $share_delta"
        after_area=$(window_area "$address")

        # Depending on which root side Dwindle assigned to the new tile, a
        # positive delta may shrink it. If so, reverse the probe and adjustment.
        if ((after_area > 0 && after_area < before_area)); then
            reverse_delta=$(format_basis_points "$((-2 * (art_share_percent - 50) * 100))")
            layout_message "splitratio $reverse_delta"
        fi
    else
        # Choose an unequal local split, but constrain it so both siblings can
        # stay within the requested area limits whenever that is already possible.
        lower_bound=$min_area
        sibling_max_lower=$((parent_area - max_area))
        ((sibling_max_lower > lower_bound)) && lower_bound=$sibling_max_lower

        upper_bound=$max_area
        sibling_min_upper=$((parent_area - min_area))
        ((sibling_min_upper < upper_bound)) && upper_bound=$sibling_min_upper

        if ((lower_bound <= upper_bound)); then
            desired_area=$(random_between "$lower_bound" "$upper_bound")
        else
            # A large early branch must be split again later. Keep this division
            # asymmetric, but not so extreme that it strands an undersized leaf.
            lower_bound=$((parent_area * 38 / 100))
            upper_bound=$((parent_area * 62 / 100))
            desired_area=$(random_between "$lower_bound" "$upper_bound")
        fi
        ratio_basis_points=$((desired_area * 10000 / parent_area))
        split_delta=$(format_basis_points "$((ratio_basis_points - 5000))")
        focus_window "$address"
        layout_message "splitratio $split_delta"

        # Occasional child swaps break up predictable left-to-right growth.
        if ((RANDOM % 3 == 0)); then
            focus_window "$address"
            layout_message 'swapsplit'
        fi
    fi
done

# Coupled tiled resizing can push a neighbor outside a limit. Recheck actual
# geometry and converge the whole composition after the tree is complete.
for ((pass = 0; pass < 4; pass++)); do
    violations=0
    for address in "${tile_addresses[@]}"; do
        area=$(window_area "$address")
        ((area > 0)) || continue

        if ((area < min_area)); then
            violations=$((violations + 1))
            nudge_tile_to_area "$address" "$((min_area + tolerance))" "$tolerance"
        elif ((area > max_area)); then
            violations=$((violations + 1))
            nudge_tile_to_area "$address" "$((max_area - tolerance))" "$tolerance"
        fi
    done
    ((violations == 0)) && break
done

if [[ -n "$old_focus" ]]; then
    hyprctl eval \
        "local w = hl.get_window(\"address:$old_focus\"); if w then hl.dispatch(hl.dsp.focus({ window = w })) end" \
        >/dev/null 2>&1 || true
fi
