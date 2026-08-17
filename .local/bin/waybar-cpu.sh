#!/usr/bin/env bash
set -euo pipefail

read_stat() {
    awk '/^cpu/{print}' /proc/stat
}

sample1=$(read_stat)
sleep 0.2
sample2=$(read_stat)

parsed=$(paste <(echo "$sample1") <(echo "$sample2") | awk '
{
    cpu = $1
    idle1 = $5 + $6
    total1 = $2+$3+$4+$5+$6+$7+$8+$9+$10+$11
    idle2 = $16 + $17
    total2 = $13+$14+$15+$16+$17+$18+$19+$20+$21+$22
    dtotal = total2 - total1
    didle = idle2 - idle1
    usage = dtotal > 0 ? (dtotal - didle) * 100 / dtotal : 0
    if (cpu == "cpu") {
        printf "OVERALL %.1f\n", usage
    } else {
        core = cpu
        sub(/^cpu/, "", core)
        printf "CORE core%-14s %5.1f%%\n", core, usage
    }
}
')

overall=$(awk '/^OVERALL/{printf "%.0f", $2}' <<< "$parsed")
cores=$(awk '/^CORE/{sub(/^CORE /,""); print}' <<< "$parsed")

jq -cn --arg text "󰘚  ${overall}%" --arg tooltip "Per-core usage:
<tt>${cores}</tt>" '{text: $text, tooltip: $tooltip}'
