# Machine-specific system state

Home configuration is always deployed as file-by-file symlinks. System files are
installed from the bootstrap script or documented here; `/etc` is deliberately not
symlinked into a user-owned Git checkout.

## SDDM login screen (no Plasma desktop)

`setup/install-sddm.sh` installs the self-contained macOS-inspired Qt 6 theme from
`setup/sddm/themes/macos/` into `/usr/local/share/sddm/themes/macos/`, and installs
`setup/sddm/10-macos.conf` into `/etc/sddm.conf.d/10-macos.conf`. These are root-owned
copies, not symlinks into this checkout. Run the script again after changing the
sources. SDDM uses Weston in kiosk mode, not KWin or Plasma, for its Wayland greeter.
`setup/sddm/weston.ini` is installed at `/etc/sddm/weston.ini`; it scales this
MacBook's 2560×1600 `eDP-1` panel by 2 for a readable Retina login screen without
changing Hyprland's separate 1.6 scale. Verify the output name before reuse.
The original SVG background and icons do not need external downloads or Apple assets.

On first deployment, `/var/lib/sddm/state.conf` preselects the current user and
**Hyprland (uwsm-managed)**. Subsequent deployments preserve the remembered state.
The theme shows no user/session pickers: it restores the saved account and pins
`sessionFile` to `/usr/share/wayland-sessions/hyprland-uwsm.desktop`, regardless of
the remembered session index. If that session is unavailable, sign-in is disabled
rather than falling back to plain Hyprland.
Password authentication remains enabled; no autologin or PAM changes are made.
The installer disables Plasma Login Manager and enables SDDM for the **next boot**,
without stopping/restarting the running login manager or terminating a session.
The generic Asahi release identity replaces the Plasma-specific identity; the
Asahi kernel, audio, firmware, platform packages, standalone apps and shared Qt/KDE
libraries remain installed. Legacy Plasma home settings are retained, not activated.

KDE Plasma and the running Plasma Login Manager are removed in a reviewed DNF
**offline** transaction, so their uninstall scripts cannot terminate the live session.
Check a pending transaction with `sudo dnf5 offline status`. To apply it immediately
when ready to end the session, use `sudo dnf5 offline reboot`. A transaction armed
using `sudo env DNF_SYSTEM_UPGRADE_NO_REBOOT=1 dnf5 offline reboot` runs at the next
normal reboot without rebooting at the time it is armed. Changing packages invalidates
a pending transaction; rerun the removal command shown by `offline status` and arm it
again before rebooting. This staging is a one-time migration step, not part of the
bootstrap or theme installer. No broad autoremove or whole-environment removal is
used, to preserve networking, firmware, fonts and apps.

## Power button opens a terminal

`/etc/systemd/logind.conf.d/90-power-button.conf` is installed from
`setup/logind-power-button.conf` with owner `root:root` and mode `0644`.
It sets `HandlePowerKey=ignore` and `HandlePowerKeyLongPress=ignore`, so logind
does not shut down the machine when the power button is pressed. Apply it with
`sudo systemctl reload systemd-logind.service`; restarting logind is unnecessary.

`.config/hypr/keybindings.lua` binds `XF86PowerOff` to the configured terminal
(Kitty), just like Super+Q, without repeating or running while the screen is locked.
The shortcut also works while modifier keys are held. Software cannot prevent the
Mac's firmware-level forced power-off from holding the physical button down.

To restore the default, remove that Hyprland binding and this `/etc` drop-in, then
reload Hyprland and logind. Normal menu/command shutdown remains available throughout.

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

## Codex Touch Bar privilege boundary

`/etc/sudoers.d/codex-touchbar` is installed from `setup/codex-touchbar.sudoers`
with owner `root:root` and mode `0440`. It grants `chihin` passwordless access to
exactly `systemctl stop tiny-dfr` and `systemctl start tiny-dfr`, allowing the
unprivileged animation player to borrow the panel and restore its normal media-key
daemon. `setup/install.sh` validates the source with `visudo` before installing it.
This machine also retains its older `%wheel ALL=(ALL) NOPASSWD: ALL` policy by owner
choice, so the feature-specific entry is redundant here but remains the reproducible
least-privilege default for other installations.
