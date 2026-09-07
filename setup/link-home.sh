#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
manifest="$repo_root/setup/home-files.txt"
backup_root=""
linked=0
unchanged=0

while IFS= read -r relative || [[ -n "$relative" ]]; do
    [[ -z "$relative" || "$relative" == \#* ]] && continue
    source_path="$repo_root/$relative"
    target_path="$HOME/$relative"

    if [[ ! -e "$source_path" && ! -L "$source_path" ]]; then
        printf 'Missing repository source: %s\n' "$source_path" >&2
        exit 1
    fi

    if [[ -L "$target_path" ]] && [[ $(readlink -f -- "$target_path") == $(readlink -f -- "$source_path") ]]; then
        ((unchanged += 1))
        continue
    fi

    mkdir -p -- "$(dirname -- "$target_path")"
    if [[ -e "$target_path" || -L "$target_path" ]]; then
        if [[ -z "$backup_root" ]]; then
            backup_root="$HOME/.local/state/asahi-rice/backups/$(date +%Y%m%d-%H%M%S)"
        fi
        backup_path="$backup_root/$relative"
        mkdir -p -- "$(dirname -- "$backup_path")"
        mv -- "$target_path" "$backup_path"
    fi

    ln -s -- "$source_path" "$target_path"
    ((linked += 1))
done < "$manifest"

printf 'Linked: %d; already correct: %d\n' "$linked" "$unchanged"
if [[ -n "$backup_root" ]]; then
    printf 'Previous files were preserved in %s\n' "$backup_root"
fi
