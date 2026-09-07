# Machine-specific system state

Home configuration is always deployed as file-by-file symlinks. System files are
installed from the bootstrap script or documented here; `/etc` is deliberately not
symlinked into a user-owned Git checkout.

## Shared exFAT volume

The macOS/Fedora shared volume is mounted by this `/etc/fstab` entry. Its UUID and the
numeric owner IDs are machine-specific and must be verified with `lsblk -f` and `id`
before reuse:

    UUID=6A79-D0DA /home/chihin/share exfat uid=1000,gid=1000,umask=022,nofail 0 0

## System-installed local software

- `mpvpaper` and `mpvpaper-holder` are built from the pinned source revision by
  `setup/install-external.sh` and installed below `/usr/local/bin`.
- Cloudflare WARP is installed from the official repo created by `setup/install.sh`.
  Registration and device identity stay outside Git.
- `lazygit` v0.64.0 is installed from its pinned upstream ARM64 release by
  `setup/install-external.sh`.
