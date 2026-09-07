#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
source /etc/os-release
arch=$(uname -m)

if [[ ${ID:-} != fedora || "$arch" != aarch64 ]]; then
    printf 'This installer targets Fedora Asahi Remix on aarch64 (found %s on %s).\n' "${PRETTY_NAME:-unknown}" "$arch" >&2
    exit 1
fi

fedora_release=$(rpm -E %fedora)
sudo dnf install -y dnf-plugins-core curl git flatpak unzip

for copr in $(sed '/^\s*#/d; /^\s*$/d' "$repo_root/setup/copr-repos.txt"); do
    sudo dnf copr enable -y "$copr"
done

sudo dnf install -y \
    "https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-${fedora_release}.noarch.rpm" \
    "https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-${fedora_release}.noarch.rpm"

sudo dnf config-manager addrepo --overwrite --from-repofile=https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo
sudo dnf config-manager addrepo --add-or-replace --id=google-chrome \
    --set=name=google-chrome \
    --set=baseurl=https://dl.google.com/linux/chrome/rpm/stable/aarch64 \
    --set=enabled=1 --set=gpgcheck=1 \
    --set=gpgkey=https://dl.google.com/linux/linux_signing_key.pub

warp_repo=$(mktemp)
trap 'rm -f -- "$warp_repo"' EXIT
curl --fail --location --silent --show-error https://pkg.cloudflareclient.com/cloudflare-warp-ascii.repo > "$warp_repo"
sudo install -m 0644 "$warp_repo" /etc/yum.repos.d/cloudflare-warp.repo
sudo rpm --import https://pkg.cloudflareclient.com/pubkey.gpg

sudo dnf upgrade --refresh -y

if rpm -q --quiet ffmpeg-free; then
    sudo dnf swap -y ffmpeg-free ffmpeg --allowerasing
fi
mapfile -t packages < <(sed '/^\s*#/d; /^\s*$/d' "$repo_root/setup/dnf-packages.txt")
sudo dnf install -y --allowerasing "${packages[@]}"

"$repo_root/setup/install-external.sh"

sudo flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
while read -r scope app _ || [[ -n "${scope:-}" ]]; do
    [[ -z "${scope:-}" || "$scope" == \#* ]] && continue
    if [[ "$scope" == system ]]; then
        sudo flatpak install --system -y flathub "$app"
    else
        flatpak install --user -y flathub "$app"
    fi
done < "$repo_root/setup/flatpak-apps.txt"

"$repo_root/setup/link-home.sh"
systemctl --user daemon-reload
while IFS= read -r unit || [[ -n "$unit" ]]; do
    [[ -z "$unit" || "$unit" == \#* ]] && continue
    systemctl --user enable --now "$unit"
done < "$repo_root/setup/user-services.txt"
sudo systemctl daemon-reload
sudo systemctl enable --now warp-svc.service

printf '\nBase setup installed. Run setup/audit.sh to check it.\n'
printf 'Cloudflare account registration is intentionally interactive: warp-cli registration new && warp-cli connect\n'
