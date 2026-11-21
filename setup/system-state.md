# System configuration

Home files are symlinked through `setup/home-files.txt`. System files are
root-owned copies, **not** symlinks into this user-owned checkout. The bootstrap
covers packages, SDDM, power-button handling and Touch Bar permissions; networking,
firewall policy, optional service reductions and storage below are machine-specific.

## SDDM login screen

`setup/install-sddm.sh` installs:

| Source | System destination |
| --- | --- |
| `setup/sddm/themes/macos/` | `/usr/local/share/sddm/themes/macos/` |
| `setup/sddm/10-macos.conf` | `/etc/sddm.conf.d/10-macos.conf` |
| `setup/sddm/weston.ini` | `/etc/sddm/weston.ini` |

Rerun the installer after changing these sources. The greeter uses Weston kiosk,
not a Plasma session. Its `eDP-1` scale is 2, independently of Hyprland's 1.6;
libinput tap-to-click and tap-and-drag are enabled for the greeter.

Install a trusted **Bibata Original Classic** Xcursor theme as a root-owned copy
in `/usr/share/icons/Bibata-Original-Classic/` before deploying. The installer
requires `cursors/left_ptr`; aliases must be relative links within the theme.
For an existing local copy:

```sh
cursor_source="$HOME/.local/share/icons/Bibata-Original-Classic"
cursor_target=/usr/share/icons/Bibata-Original-Classic
sudo install -d -o root -g root -m 0755 "$cursor_target"
sudo cp -a --no-preserve=ownership "$cursor_source/." "$cursor_target/"
sudo chown -hR root:root "$cursor_target"
sudo find "$cursor_target" -type d -exec chmod 0755 {} +
sudo find "$cursor_target" -type f -exec chmod 0644 {} +
sudo restorecon -RF "$cursor_target"
```

The theme restores the saved account, hides account/session pickers, and pins
`/usr/share/wayland-sessions/hyprland-uwsm.desktop`. Missing that session disables
sign-in rather than falling back to plain Hyprland. Password authentication stays
enabled; no autologin or PAM changes are made. UWSM is required for graphical
session targets, portals, polkit and the keyring.

The installer enables SDDM for the **next boot** without stopping the live login
manager. It does not automatically remove Plasma. If explicitly removing an active
desktop/login manager, use a reviewed DNF offline transaction rather than risking
uninstall hooks terminating the session. Check with `sudo dnf5 offline status`;
`sudo dnf5 offline reboot` applies it and ends the session. Do not broadly autoremove
shared Asahi, networking, firmware or Qt/KDE application dependencies.

See the [theme README](sddm/themes/macos/README.md) for requirements and smoke tests.

## Wi-Fi and DNS

- `iwd.service` manages Wi-Fi authentication, DHCP and IPv6 on `wld0`.
  NetworkManager and wpa_supplicant are disabled/masked; systemd-networkd is
  disabled. Retained libnm/libnma libraries are not network-management daemons.
- `setup/iwd-main.conf` is copied to `/etc/iwd/main.conf`. It enables built-in
  networking, systemd name resolution, per-network MAC randomization and IPv6.
  Disconnected scanning starts at 30 seconds, capped at 300 seconds.
- `setup/resolved-low-power.conf` is copied to
  `/etc/systemd/resolved.conf.d/90-low-power.conf`: LLMNR off, mDNS resolver-only
  (`MulticastDNS=resolve`), caching on.
- `/etc/resolv.conf` points to `/run/systemd/resolve/stub-resolv.conf`
  (`127.0.0.53`). No static WARP DNS pin or global fallback servers are configured.

Resolved runs in **every power profile**. iwd supplies DHCP DNS/search domains;
WARP supplies its DNS route while connected and removes it on disconnect.
Network DNS then takes over. More-specific network search domains can take
precedence over WARP's `~.` route: this is split DNS, not a promise that every query
uses WARP. Application DoH and explicit DNS servers are outside this policy.
WARP and Tailscale are managed independently of iwd.

Use Noctalia's native network popup or `iwctl` for Wi-Fi management. Full static
IP/DNS/802.1X settings live in `/var/lib/iwd/*.psk`, `*.open` or `*.8021x`;
non-simple SSIDs use encoded filenames. Profiles and credentials stay root-only
(directory `0700`, files `0600`) and must never enter Git. For careful editing:

```sh
sudo ls /var/lib/iwd
SUDO_EDITOR='vim -N -u NONE -U NONE -n -i NONE --cmd "set nomodeline nobackup nowritebackup noundofile"' \
  sudoedit -- '/var/lib/iwd/SSID.psk'
```

Choose the real filename and reconnect after changes. See `iwd.network(5)`.
Noctalia's Bluetooth popup uses BlueZ; `bluetoothctl` is available for CLI control.

### Client-only multicast DNS

`setup/mdns-client-only.nft` is installed at `/etc/nftables/mdns-client-only.nft`;
`setup/mdns-client-only.service` is installed under `/etc/systemd/system/` and
enabled. This oneshot service owns only the `inet mdns_client_only` table, not
firewalld or VPN rules.

On `wld0`, it drops incoming multicast UDP/5353 **questions** (DNS QR=0), retaining
answers, unsolicited announcements, outgoing queries, unicast packets and ordinary
DNS. Resolver-only mode still permits `.local` lookups. This reduces userspace
query handling, not radio/kernel reception or all multicast traffic.
**Disable the filter if this machine must advertise/respond to mDNS services.**

```sh
sudo nft list table inet mdns_client_only
sudo systemctl disable --now mdns-client-only.service
# Re-enable deliberately:
sudo systemctl enable --now mdns-client-only.service
```

Stopping the service removes only its own table. The bootstrap does not install
this firewall policy or switch network managers automatically. See
[RFC 6762 sections 5–6](https://www.rfc-editor.org/rfc/rfc6762.html).

### Network verification and recovery

Check `systemctl status iwd systemd-resolved`, `iw dev wld0 get power_save`,
`warp-cli status`, `resolvectl status`, `dig example.com`,
`getent ahostsv4 example.com`, and HTTPS connectivity. Use a known local host with
`resolvectl --cache=no --protocol=mdns --interface=wld0 query HOST.local`.
Verify uncached DNS with WARP both connected and disconnected when safe.

Root-only network backups and a rollback script live in
`/var/lib/network-power-migration/`. To restore NetworkManager, reinstall it
**while iwd still provides Wi-Fi**, then use the reviewed local rollback script:

```sh
sudo dnf5 install NetworkManager NetworkManager-wifi
sudo bash /var/lib/network-power-migration/rollback.sh
```

The script refuses if NetworkManager is absent. It restores the original manager
and resolver policy and disables the client-only filter; migrated iwd profiles
remain inactive. Verify these local backup files before relying on recovery.

## Power profiles and optional idle services

`tuned.service` and `tuned-ppd.service` provide performance/balanced/power-saver
through the power-profiles D-Bus interfaces. The bootstrap installs/enables them.
Profiles do not stop resolved, change DNS policy or alter wallpaper rotation.
Noctalia is the active shell; retained Waybar power helpers are not the deployed UI.

ModemManager is disabled/masked on this machine; automatic ABRT collectors are
disabled. Normal systemd coredumps, journald, auditd, SELinux, firewalld, Bluetooth,
VPNs and speaker protection remain enabled. Apple CPU idle, `schedutil` and Wi-Fi
power save remain in use. No battery-life or wattage saving is established here.
The root-only optional-service backup is
`/var/lib/network-power-migration/idle-services-before.json`.

To restore the optional services:

```sh
sudo systemctl unmask ModemManager.service
sudo systemctl enable --now ModemManager.service abrtd.service \
  abrt-journal-core.service abrt-oops.service abrt-xorg.service
```

The four `.config/autostart/` `Hidden=true` overrides suppress Blueman, imsettings,
Xwayland Video Bridge and the SELinux troubleshooter tray. Removing an override
allows its system launcher to run. This does not disable SELinux enforcement.
Hyprland starts IBus directly; no separate Fcitx startup is active.

## Power button

`setup/logind-power-button.conf` is installed as
`/etc/systemd/logind.conf.d/90-power-button.conf`, root-owned mode `0644`.
`HandlePowerKey=ignore` and `HandlePowerKeyLongPress=ignore` leave the key to
Hyprland, where `XF86PowerOff` opens Kitty like Super+Q. Apply logind changes with
`sudo systemctl reload systemd-logind.service`, not a restart.

To undo, remove the Hyprland binding and the system drop-in, then reload Hyprland
and logind. Menu/command shutdown remains available. Holding the physical button
can still force power-off in firmware.

## Applications and storage

- WARP comes from Cloudflare's official repository; registration and device
  identity stay outside Git. `setup/install-external.sh` installs the pinned
  upstream ARM64 lazygit release recorded in `setup/external-sources.tsv`.
- WeChat uses a separately installed **user Flatpak**. Its desktop override enables
  X11, disables Wayland, selects Qt XCB/IBus and unsets experimental IBus sync mode.
  The RPM launcher is hidden. Main-window rules ignore maximum-size hints without
  forcing tiling/floating; subwindows keep their own hints. Test click alignment,
  resizing and Chinese input together.
- The LibreWolf repository backup is `/etc/yum.repos.d/librewolf.repo.disabled`;
  LibreWolf and its profile are untouched. Renaming it back to `librewolf.repo`
  re-enables the repository. Inspect with `dnf -C repo list --all`.
- Shared exFAT storage is mounted at `~/share`. Its fstab entry is machine-specific:

  ```fstab
  UUID=6A79-D0DA /home/chihin/share exfat uid=1000,gid=1000,umask=022,nofail 0 0
  ```

  Verify UUID/owner IDs with `lsblk -f` and `id` before reuse. `._*` AppleDouble
  files are metadata, not playable media. Partition creation/resizing is not a
  bootstrap operation.

## Desktop-specific references

- [Noctalia](noctalia.md) owns wallpaper rendering/rotation and native launch/capture.
  Do not enable the retained swaybg unit or random-wallpaper timer alongside it.
- [Touch Bar](../docs/touchbar.md) documents the narrow `tiny-dfr` sudo boundary,
  notification service and local player build.
- [Gentoo boot](gentoo-boot.md) documents the separate ESP and one-shot reboot helper.

Retired `warp-resolv.conf`, `resolved-warp-dns.conf`,
`resolved-{power-saver,performance,power-saver-at-boot}.service` and
`power-profile-resolver.sudoers` sources are inert placeholders, **not installation
instructions**. Do not install them or restore DNS/power-profile coupling.
