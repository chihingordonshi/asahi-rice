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
The same Weston file explicitly enables libinput devices, touchpad tap-to-click
and tap-and-drag for the greeter. SDDM uses **Bibata Original Classic** at size 24,
configured in `setup/sddm/10-macos.conf`, matching the existing Hyprland cursor.
These input/cursor settings take effect on the next greeter launch; they do not
alter Hyprland's input preferences. The original SVG background and icons do not
need external downloads or Apple assets.

Before running the installer on a new host, install a trusted copy of the
Bibata Original Classic Xcursor theme system-wide. This machine uses the existing
v2.0.6 assets, copied from the user's theme rather than downloaded or loaded from
home by the greeter. Cursor aliases must be relative links within the theme.
For an existing local installation:

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

The installer checks for the system cursor's `cursors/left_ptr` before deploying
SDDM. Cursor binaries are not stored in Git; existing Adwaita packages are not
uninstalled.

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

## Standalone iwd Wi-Fi and low-idle DNS

Wi-Fi authentication, IPv4 DHCP and IPv6 are managed by `iwd.service`.
**DNS follows the normal network/VPN configuration**, without a static WARP pin.
iwd publishes DHCP DNS/search domains to `systemd-resolved`; WARP installs its own
DNS route while connected and removes it on disconnect, allowing network DNS to
take over. Resolved stays enabled and running in every power profile, including
power-saver, so DNS fallback and `.local` remain available.
NetworkManager, its dispatcher/wait-online units, and wpa_supplicant are stopped,
disabled and masked to prevent competing managers. `systemd-networkd` stays
disabled; iwd's built-in network configuration avoids another daemon.
The NetworkManager daemon, plugins, TUI, applet and editor were subsequently
removed (10 packages, about 13 MiB installed size) without unrelated autoremove.
`NetworkManager-libnm` and `libnma` remain because removing them would also remove
Blueman and firewall-config; these are libraries, not idle daemons. Original
connection files and a root-only configuration archive remain for rollback.
WARP and Tailscale remain independently managed, not iwd profiles.

Root-owned copies of these configuration sources are installed, not symlinks:

- `setup/iwd-main.conf` → `/etc/iwd/main.conf`: built-in IP configuration,
  `NameResolvingService=systemd`, per-network MAC randomization, IPv6 and a 30-second
  initial disconnected scan interval (maximum 300 seconds). DHCP DNS/search domains
  are passed to resolved. Automatic reconnection and roaming remain enabled.
  The Broadcom default interface `wld0` is preserved.
- `setup/resolved-low-power.conf` →
  `/etc/systemd/resolved.conf.d/90-low-power.conf`: disables LLMNR, keeps mDNS in
  **resolver-only** mode (`MulticastDNS=resolve`) and keeps DNS caching enabled.
  With resolved running, `.local` works without advertising or answering questions.
- `/etc/resolv.conf` is restored to the managed stub symlink
  `/run/systemd/resolve/stub-resolv.conf` (`127.0.0.53`), not a static WARP file.
  The `95-warp-dns.conf` override is removed. Neither global DNS servers nor
  fallback/domain-routing policy are pinned by the local configuration.

NSS remains authselect-managed and unchanged. Resolved handles ordinary DNS and
mDNS; both NSS clients and direct resolv.conf users follow its dynamic routing.
The current network supplies `bsn.net`, which can legitimately take precedence
for campus names over WARP's `~.` route. This is normal split DNS, not a guarantee
that every query goes through WARP whenever connected. Application-specific DoH or
explicitly selected DNS servers are outside this policy.

The initial experiment on 2026-11-02 disabled both LLMNR and mDNS. Matched
40-second samples showed CPU dropping from 3.15% of one core to 0.00% at the
measurement resolution, and voluntary context switches from 55.95/s to 0.57/s.
A later sample with iwd connected gave 0.025% resolver CPU and 0.35 voluntary
switches/s; iwd used 0.00% CPU. **Those are historical results for the initially
rejected mDNS-disabled configuration**, which broke required `.local` lookups.
mDNS was subsequently restored to resolver-only mode; the near-zero sample is
not a measurement of the current configuration. A later power-saver experiment
stopped the daemon entirely, but that policy has been retired to restore normal
network/VPN DNS fallback. These are activity measurements, not measured
wattage/battery life. A subsequent 40-second sample with resolver-only
mDNS restored (including one service-discovery verification) measured 1.35%
resolver CPU and 37.40 voluntary switches/s; results depend on LAN traffic.
`iw dev wld0 get power_save` reports on.

Resolver-only mode alone disables responding, not reception: lookup replies must
still come in, and mDNS replies normally use multicast. Without the client-only
filter below, unrelated queries and unsolicited announcements still reach the
multicast socket. A blanket inbound UDP/5353 block
would break `.local`; ordinary established-connection rules do not reliably match
multicast replies. The client-only filter below instead drops multicast
**questions only**, retaining all incoming answers. See
[RFC 6762 sections 5–6](https://www.rfc-editor.org/rfc/rfc6762.html).

Eight saved station profiles (including a hidden phone network) were migrated to
root-only `/var/lib/iwd` files, mode 0600 under a 0700 directory. The active SSID's
MAC was preserved with its `AddressOverride`, retaining its DHCP identity.
`ANDOVER11-test` had no available saved credential and was not converted. The two
old NetworkManager hotspot profiles were retained but not converted. Never store
these passwords, identity material or machine-specific profiles in Git.

### Waybar network controls

- **Left-click the network icon:** `~/.local/bin/impala` 0.8.1. `Tab` switches
  panels, `s` scans, Enter connects/disconnects; in New Networks, `n` connects a
  hidden SSID; in Known Networks, `t` toggles autoconnect and `d` forgets a network.
- **Right-click:** the upstream `iwctl` interactive console, including connection
  details, hidden networks, saved-network properties, adapters, WPS and hotspot
  commands. Type `help` to list available commands. There is no middle-click action.
- There is no custom networking application or wrapper. Both utilities run only
  when opened, so they add no idle polling daemon. This is Wi-Fi management,
  not a replacement UI for NetworkManager-specific VPN/wired
  profiles. `nm-applet` is removed from Hyprland startup and suppressed via an
  XDG autostart override; Waybar's network status itself uses netlink, not NM.

Impala was built user-locally from the reviewed, pinned crates.io package using
`cargo install impala --version 0.8.1 --locked --root "$HOME/.local"`.
`iwctl` was already installed as part of iwd. The new XDG autostart override is
listed in `setup/home-files.txt`; system network switching is intentionally not
done automatically by the generic bootstrap installer.

For full credential/static IP/DNS/IPv6/802.1X editing beyond the properties exposed
by `iwctl`, use the existing `sudoedit` and Vim from a terminal (not a separate
Waybar click action):

```sh
sudo ls /var/lib/iwd
SUDO_EDITOR='vim -N -u NONE -U NONE -n -i NONE --cmd "set nomodeline nobackup nowritebackup noundofile"' \
  sudoedit -- '/var/lib/iwd/SSID.psk'
```

Choose the actual `.psk`, `.open` or `.8021x` filename; non-simple SSIDs have
hex-encoded filenames. Vim `:wq` saves and `:q!` cancels. This runs the editor as
the caller, without plugins, modelines, swap, undo, viminfo or backup files.
Reconnect to apply IP/DNS/security changes. See `man 5 iwd.network` for all keys.
Impala/iwctl are Wi-Fi managers, not graphical full-profile form editors.

### Verification and rollback

Verify iwd, `iw dev wld0 get power_save`, `warp-cli status`, `dig example.com`
(server should be the `127.0.0.53` stub), `getent ahostsv4 example.com`,
`resolvectl status` and an HTTPS request. Check mDNS with
`resolvectl --cache=no --protocol=mdns --interface=wld0 query chsrv.local`.

After removing the static pin, iwd supplied `172.16.75.9` / `172.16.75.10` and
`bsn.net` on `wld0`. WARP connected with its own local DNS proxies and `~.` route;
there were no global static DNS servers. A brief guarded WARP disconnect verified
that an uncached, ordinary `example.com` query selected `wld0` without forcing an
interface, NSS worked, and public HTTPS returned 200. After reconnection, WARP
was healthy, its DNS route returned, and uncached DNS/HTTPS worked again.
The managed resolv.conf symlink survived both transitions. In power-saver,
uncached `chsrv.local` returned `172.16.9.135` through mDNS and local HTTP returned
302. Resolved and both sockets are enabled, with the old runtime masks removed;
the boot stop helper and its sudo grant are removed. All three live Waybar profile
transitions preserved resolved's PID and the wallpaper configuration checksum.
The 41 relevant networking/desktop regression tests, shell/unit syntax checks,
sudoers validation and scoped whitespace checks passed. The three-minute DNS/WARP
recovery guard was cancelled after the connectivity checks. A physical reboot was
not performed.

Original service/resolver state and root-only migration records are in
`/var/lib/network-power-migration/`, including
`networkmanager-config-before-removal.tar.gz` and the original RPM package list.
Since NetworkManager was removed, reinstall it **while iwd still provides Wi-Fi**
before restoring the original system networking:

```sh
sudo dnf5 install NetworkManager NetworkManager-wifi
sudo bash /var/lib/network-power-migration/rollback.sh
```

The rollback script now refuses before changing networking if NetworkManager is
not installed. When proceeding, it checks the old WARP-only DNS restore helper
(which is now a no-op because that policy was already undone), then disables the
client-only mDNS filter.

It then stops/disables iwd, unmasks/re-enables NetworkManager (and its original
related units), removes only the two new system configuration copies, and reloads
resolved to restore the previous multicast policy. Original NetworkManager
profiles are untouched; migrated iwd profiles remain available but inactive.
The home/Waybar utilities are separate: to restore the old tray UI, remove the
`~/.config/autostart/nm-applet.desktop` override, restore the old Waybar click
command and Hyprland `nm-applet` startup line, then run `nm-applet`.

References: local `iwd.config(5)`, `iwd.network(5)`, `iwctl(1)`, `resolved.conf(5)`;
[upstream iwd configuration](https://kernel.googlesource.com/pub/scm/network/wireless/iwd/+/master/src/iwd.config.rst),
[Impala](https://github.com/pythops/impala).

## Additional idle CPU and RAM reductions

The major CPU problem was the legacy shell Waybar auto-hide controller, not the
Wi-Fi daemon: its 10 Hz loop repeatedly spawned `pgrep`, `date`, three `hyprctl`
clients, two `jq` processes and `sleep`. `.config/hypr/waybar.lua` now uses the
installed Hyprland 0.57 native Lua timer/query API. It checks cursor state in-process
at 100 ms, spawning only on actual visibility transitions. Super+B, empty-workspace
visibility, 200 ms top-edge reveal, 72 px hover, startup grace and config-reload
state are preserved. The legacy shell file remains for compatibility but is no
longer started. Existing user-disabled clock/quickmenu startup lines were preserved.

Waybar uses native `cpu` (5 s) and `memory` (15 s) modules instead of recurring shell
pipelines. Memory process details are available on demand by clicking it for btop.
The minute-resolution clock now updates each minute; its tooltip no longer claims
live seconds. Fcitx polls every 3 s, and power-profile status every 30 s (clicks
still refresh immediately).
Brightness/volume fallback polling is 10/5 s; existing helper/hotkey changes still
refresh immediately through signals, preserving perceptual brightness and OSDs.

A 30-second before sample and a subsequent 60-second sample gave:

| CPU, percent of one core | Before | After desktop changes |
| --- | ---: | ---: |
| Hyprland service group, including spawned descendants | 35.82% | 2.16% |
| Waybar service group, including helpers | 3.53% | 1.01% |

These are live-desktop activity samples, not isolated whole-system idle-power
measurements. The before/after windows differ, and LAN traffic varies. Agent and
terminal activity is outside these service groups. No wattage or battery-life
saving is claimed.

With no cellular modems detected, `ModemManager.service` is stopped, disabled and
masked against D-Bus activation. Automatic ABRT journal/core/oops/Xorg collectors
(`abrtd`, `abrt-journal-core`, `abrt-oops`, `abrt-xorg`) are stopped and disabled.
Their combined prior proportional resident footprint was about **86 MiB PSS**;
this is not a guaranteed physical-memory delta. Normal systemd coredumps,
journald, auditd, SELinux enforcement, firewalld, Bluetooth, VPNs and speaker
protection remain enabled. No generic x86 power knobs or aggressive PCIe changes
were applied; Apple CPU idle, `schedutil` and Wi-Fi power save remain in use.
Service state before changes is recorded root-only in
`/var/lib/network-power-migration/idle-services-before.json`.

Restore those optional services with:

```sh
sudo systemctl unmask ModemManager.service
sudo systemctl enable --now ModemManager.service abrtd.service \
  abrt-journal-core.service abrt-oops.service abrt-xorg.service
```

### Client-only multicast DNS filter

`setup/mdns-client-only.nft` is installed as `/etc/nftables/mdns-client-only.nft`,
with `setup/mdns-client-only.service` installed under `/etc/systemd/system/` and
enabled. The service is **oneshot**, not a polling daemon. It owns only the
`inet mdns_client_only` nftables table and does not flush firewalld/VPN rules.

On physical Wi-Fi `wld0`, it drops only incoming UDP/5353 packets addressed to
IPv4/IPv6 mDNS multicast groups with DNS QR=0 (questions). DNS QR=1 answers,
including unsolicited announcements, outgoing queries, unicast packets and normal
DNS are unchanged. This avoids waking userspace to parse other devices' questions.
It does not prevent Wi-Fi hardware/kernel reception or eliminate response traffic.
**Trade-off:** no mDNS responder on this machine can hear those multicast queries;
disable the filter if this host must advertise/respond to local services.

A 60-second trial reduced resolved from 1.60% CPU / 34.20 voluntary switches/s to
1.30% / 13.65 switches/s, while dropping about 3,600 incoming questions. This is
traffic-dependent, not a guarantee of proportional power savings. Fresh uncached
`chsrv.local` resolution, general DNS-SD responses, local HTTP 302, public HTTPS
200, WARP, nft syntax, service reload and stop/start rollback were verified.
The IPv6 rule was syntax/QR-logic checked; no IPv6-only test host was provided.

Inspect or reversibly disable the filter with:

```sh
sudo nft list table inet mdns_client_only
sudo systemctl disable --now mdns-client-only.service
```

Re-enable with `sudo systemctl enable --now mdns-client-only.service`. Stopping it
removes only its own table. With resolved running, resolver-only `.local` support
remains enabled either way. No host addresses were pinned, and incoming answers
are not restricted to one test server. The generic bootstrap does not automatically install this
machine-specific firewall policy or switch networking.

## Waybar power profiles

Fedora's `tuned` and `tuned-ppd` packages provide the power-profile backend;
`tuned.service` and `tuned-ppd.service` are enabled and running. Replicate with:

```sh
sudo dnf install tuned-ppd
sudo systemctl enable --now tuned.service tuned-ppd.service
```

`tuned-ppd` exposes both `net.hadess.PowerProfiles` and
`org.freedesktop.UPower.PowerProfiles` on the system bus. Waybar's custom helpers
use the former to read and cycle performance / balanced / power-saver; their
rocket / scale / leaf symbols are monochrome Nerd Font glyphs, not color emoji.
There are no per-profile color overrides. The active profile remains a runtime
choice, not a setting pinned by the bootstrap. On this machine all three profiles
are advertised by the backend. Changing profiles no longer switches the wallpaper
to swaybg; the selected wallpaper backend stays unchanged in every profile.

### DNS is independent of power profiles

The WARP-only DNS pin and resolver power-switching experiment have been undone.
Waybar now changes only the CPU power profile; rapid clicks remain serialized with
a runtime flock. It does not stop/start/mask resolved or change the wallpaper.
Resolved remains running in power-saver, balanced and performance. Stopping it
would break the restored DHCP-DNS fallback, so its old profile and boot hooks and
the extra sudo grant have also been removed from the system. No replacement DNS
package, polling helper or background profile listener was installed.

The following tracked sources are **retired, inert placeholders, not installation
instructions**: `setup/warp-resolv.conf`, `setup/resolved-warp-dns.conf`,
`setup/resolved-{power-saver,performance,power-saver-at-boot}.service`, and
`setup/power-profile-resolver.sudoers`. They contain no DNS pins, resolver-stop
commands, enableable boot action or sudo grant. Do not install them.

The root-only pre-pin copies remain under
`/var/lib/network-power-migration/warp-dns-before/`. Its restore script was run
successfully and its `applied` marker cleared; later calls are no-ops. Full
NetworkManager rollback still refuses to stop iwd until NM has been reinstalled.

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
