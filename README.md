# asahi-rice

Live configuration for Chi Hin's M1 MacBook running **Fedora Asahi Remix**.
Deployed home files are symlinked into this checkout; package, repository, Flatpak,
and user-service manifests live in [`setup/`](setup/).

## Current desktop

- **Hyprland**, configured in Lua, started through **UWSM** from SDDM.
- **Native Noctalia** provides the bar, launcher, network/Bluetooth/audio popups,
  screenshots, and recursive wallpaper rotation every 15 minutes.
- **Mako** handles notifications; **hypridle/hyprlock** lock after 15 minutes
  and before suspend. Idle locking leaves the display awake.
- **IBus + Rime Ice** provide English/Chinese input, switched per input context
  with Super+R. The keyboard button beside the tray restarts a stuck IBus daemon.
- **Standalone iwd** manages Wi-Fi; **systemd-resolved** follows network/VPN DNS.
  **tuned-ppd** provides power profiles independently of DNS and wallpapers.
- **Kitty**, Dolphin, Zsh/Powerlevel10k, Qt/Kvantum and GTK settings provide the
  application environment. Fastfetch is the active system-info tool.
- Codex and interactive Pi completions share an alternating train/vines
  **Touch Bar** notification service; overlapping completions are skipped.

Waybar, Fcitx and other inactive configurations remain in the tree, but their
presence does not mean they are deployed. **`setup/home-files.txt` is the deployment
list**, not every tracked path. The optional [KDE booth setup](docs/kde-fair-booth.md)
is separate from the default Hyprland session.

## Setup

Review the manifests and scripts before running them on another machine:

| File | Purpose |
| --- | --- |
| [`setup/copr-repos.txt`](setup/copr-repos.txt) | COPR repositories; Hyprland comes from `lionheartp/Hyprland` |
| [`setup/dnf-packages.txt`](setup/dnf-packages.txt) | Explicit RPM packages |
| [`setup/flatpak-apps.txt`](setup/flatpak-apps.txt) | Flatpak application IDs and installation scopes |
| [`setup/external-sources.tsv`](setup/external-sources.tsv) | Pinned external software sources |
| [`setup/home-files.txt`](setup/home-files.txt) | File-by-file home symlinks |
| [`setup/user-services.txt`](setup/user-services.txt) | User units to enable |

Before installing:

1. Verify the panel/output settings in `.config/hypr/monitors.lua`
   (`eDP-1`, `2560x1600@60`, scale `1.6`), US keyboard settings in `input.lua`,
   and absolute wallpaper/screenshot paths in `.config/noctalia/config.toml`.
2. Install JetBrains Mono Nerd Font locally and refresh `fc-cache`. SDDM also
   needs a root-owned **Bibata Original Classic** cursor theme; see
   [system configuration](setup/system-state.md#sddm-login-screen).
3. Review personal Git identity, desktop launchers, and the username in
   `setup/codex-touchbar.sudoers`.
4. **On a replica, omit `asahi-rice-sync.timer` and its service/home links.**
   The supplied timer automatically commits and pushes to Chi Hin's repository.
   The installer enables all units listed in `setup/user-services.txt`.
5. Supply Rime Ice dictionaries/Lua and learned data separately. Existing
   `~/rime` data can be linked as `~/.config/ibus/rime`; never share the live
   database between IBus and Fcitx concurrently.

```sh
# Installs/upgrades packages, configures system files, links home files,
# and enables services. Uses sudo; review before running.
setup/install.sh
```

The installer configures SDDM for the next boot without stopping the current
session. It does **not** reproduce partitioning, the iwd migration, or every
machine-specific system adjustment; those are described in
[`setup/system-state.md`](setup/system-state.md).
Cloudflare registration is interactive: `warp-cli registration new && warp-cli connect`.
WeChat is a separately installed user Flatpak, not part of the bootstrap manifest;
its launcher selects X11/IBus. LocalSend is system-scoped; WPS 365 is user-scoped
because its extra-data installer fails system-wide SELinux labeling here.

To deploy home files without installing packages:

```sh
setup/link-home.sh
setup/configure-ibus.sh  # Run in the user session.
```

Replaced files are preserved under `~/.local/state/asahi-rice/backups/`.
Linking is additive: removing a manifest entry does not remove its old home link.

**Use “Hyprland (uwsm-managed)”, not plain Hyprland.** The SDDM theme pins
`/usr/share/wayland-sessions/hyprland-uwsm.desktop`. UWSM activates the graphical
session targets needed by portals, polkit and the secret-service keyring.

## Everyday controls

| Shortcut | Action |
| --- | --- |
| Right Command | Escape in Hyprland; both Option keys remain Alt, Caps Lock remains Super |
| Super+Q / power button | Kitty |
| Super+D | Noctalia launcher |
| Super+A / Super+Shift+A | Region / all-output screenshot; saves PNG and copies to clipboard |
| Super+R | English / Rime |
| Super+X / Right Option+/ | Pin/unpin the bar |
| `wallpaper [connector]` | Select a random wallpaper through Noctalia |

The bar stays visible on empty/floating-only workspaces and hides on tiled ones,
without top-edge reveal. Pinning reserves its 36px height. A delayed/blank workspace
widget after showing the bar remains unresolved; see [Noctalia](setup/noctalia.md).

Zoom meeting invites opened through the desktop (including `xdg-open`) go to the
Zoom Web App in Brave Profile 1. Other web links still open normally in Brave.
Clicks inside an existing browser tab only reach the desktop handler if Zoom
hands off a `zoommtg:` or `zoomus:` link. To undo the routing, restore `brave-browser.desktop`
for HTTP and HTTPS and remove the two Zoom scheme defaults in `~/.config/mimeapps.list`.

## Maintenance and reference

- [Noctalia configuration and checks](setup/noctalia.md)
- [System configuration and recovery](setup/system-state.md)
- [Codex/Pi Touch Bar setup and player rebuilds](docs/touchbar.md)
- [Gentoo boot and `reboot-gentoo`](setup/gentoo-boot.md)
- [`which-one`: installed package lookup](docs/which-one.md)
- [Mouse acceleration and disabled custom curve](docs/macos-mouse-acceleration.md)
- [SDDM theme](setup/sddm/themes/macos/README.md)

```sh
python3 -m unittest discover -s tests
bun test tests/pi-touchbar.test.ts
```

`setup/audit.sh` additionally checks live deployment, packages, codecs and services.
It also invokes the narrow sudo permission to start `tiny-dfr`; it is not a purely
read-only check. Reload Hyprland Lua with `hyprctl reload config-only` and inspect
`hyprctl configerrors`; startup commands only run at login. Avoid killing live UI
processes just to reload configuration.

Credentials, browser profiles, Rime learned data, caches and wallpaper media stay
outside Git. `.gitconfig` contains public identity and the `gh` helper command,
not the GitHub token. The personal `asahi-rice-sync` timer commits and pushes
tracked-home changes daily; see [its script](.local/bin/asahi-rice-sync).
