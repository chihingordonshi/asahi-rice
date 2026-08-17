#!/usr/bin/env bash
set -euo pipefail

read -r total avail <<< "$(awk '/^MemTotal:/{t=$2} /^MemAvailable:/{a=$2} END{print t, a}' /proc/meminfo)"
percentage=$(( (total - avail) * 100 / total ))
used_mb=$(( (total - avail) / 1024 ))
total_mb=$(( total / 1024 ))

top=$(/usr/bin/ps -eo comm,rss --sort=-rss --no-headers | head -5 | awk '{
    gsub(/&/, "\\&amp;", $1); gsub(/</, "\\&lt;", $1); gsub(/>/, "\\&gt;", $1)
    printf "%-20s %6.0f MB\n", $1, $2/1024
}')

jq -cn --arg text "󰍛  ${percentage}%" --arg tooltip "Memory: ${used_mb} MB / ${total_mb} MB (${percentage}%)

Top processes:
<tt>${top}</tt>" '{text: $text, tooltip: $tooltip}'
