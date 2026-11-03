#!/usr/bin/env bash
set -euo pipefail

clone_pinned() {
    local url=$1 target=$2 revision=$3
    if [[ -d "$target/.git" ]]; then
        if [[ -n $(git -C "$target" status --porcelain) ]]; then
            printf 'Refusing to replace modified checkout: %s\n' "$target" >&2
            return 1
        fi
        git -C "$target" fetch origin "$revision"
    elif [[ -e "$target" ]]; then
        printf 'Refusing to replace non-Git path: %s\n' "$target" >&2
        return 1
    else
        mkdir -p -- "$(dirname -- "$target")"
        git clone "$url" "$target"
        git -C "$target" fetch origin "$revision"
    fi
    git -C "$target" checkout --detach "$revision"
}

clone_pinned https://github.com/romkatv/powerlevel10k.git \
    "$HOME/.local/share/powerlevel10k" 9253fb1c5034410c43a0c681ff8294181c54016c
clone_pinned https://github.com/marlonrichert/zsh-autocomplete.git \
    "$HOME/.local/share/zsh-autocomplete" 027cdab14451e98c9d36d72b1f79d9488ac88e46

lazy_work_dir=$(mktemp -d)
curl --fail --location --silent --show-error \
    --output "$lazy_work_dir/lazygit.tar.gz" \
    https://github.com/jesseduffield/lazygit/releases/download/v0.64.0/lazygit_0.64.0_Linux_arm64.tar.gz
tar -xzf "$lazy_work_dir/lazygit.tar.gz" -C "$lazy_work_dir" lazygit
sudo install -m 0755 "$lazy_work_dir/lazygit" /usr/local/bin/lazygit
rm -rf -- "$lazy_work_dir"

font_dir="$HOME/.local/share/fonts/JetBrainsMonoNerdFont"
if ! fc-list | grep -F 'JetBrainsMono Nerd Font' >/dev/null; then
    work_dir=$(mktemp -d)
    trap 'rm -rf -- "$work_dir"' EXIT
    curl --fail --location --silent --show-error \
        --output "$work_dir/JetBrainsMono.zip" \
        https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.0/JetBrainsMono.zip
    mkdir -p -- "$font_dir"
    unzip -q "$work_dir/JetBrainsMono.zip" -d "$font_dir"
    fc-cache -f "$font_dir"
fi
