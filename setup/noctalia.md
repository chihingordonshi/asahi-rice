# Native Noctalia shell

Verified with Fedora's `noctalia` 5.4.1 and Hyprland 0.57.2 on Fedora Asahi Remix.
Follow the [Hyprland guide](https://docs.noctalia.dev/noctalia/compositor-settings/hyprland/)
selectively: existing shortcuts, window gaps, opacity, and rounding are preserved.
No Quickshell, plugins, or system service changes are required.

## Configuration and startup

- `.config/noctalia/config.toml`: minimal top bar, native network/Bluetooth/audio
  popups, launcher, native screen capture, and wallpaper selection/rotation.
  IBus remains on Super+R, not the bar.
- `.config/noctalia/palettes/Waybar.json`: fixed dark/lavender colors matching the
  previous bar. Both palette variants are required by the installed native loader;
  both deliberately use the same dark colors.
- `.config/hypr/noctalia-shell.lua`: official no-animation layer rule, floating
  settings window, tiled-only hiding without edge reveal, and Super+B/Super+X pin/unpin
  with an immediate IPC refresh.
- `autostart.lua` starts `noctalia` once at session startup. Legacy Waybar files
  remain as historical source, but are no longer deployed or installed.
- Noctalia owns wallpaper rendering. Random rotation runs every **900 seconds**,
  recursively under `/home/chihin/Pictures/Wallpapers`. Change this absolute path
  when deploying to another account. Click the wallpaper button beside the tray
  for an immediate native `wallpaper-random` action. The Zsh `wallpaper` function
  and `.local/bin/random-wallpaper` send the same IPC; optionally pass a connector
  such as `wallpaper eDP-1`. `random-wallpaper.sh` is a compatibility alias, not a
  renderer. No separate image scanner, state file, service restart, or timer is needed.

Workspace events reconcile visibility immediately; a 200ms fallback timer reads
native compositor objects, not shell commands. Noctalia's global shell animations
are disabled (including popup transitions), so workspace switches do not slowly
slide the bar away. Native auto-hide and workspace-switch reveal stay disabled.
Empty and floating-only current workspaces remain visible; a mapped, non-hidden
**tiled** window explicitly hides the bar, blocking top-edge/pointer reveal. An active special
workspace takes precedence. Super+B and Super+X both toggle pinned visibility and
force fresh visibility/reservation IPC. Pinning keeps the bar shown through window
polls and workspace switches, reserving its 36px height above tiled windows.
Unpinning releases the gap and immediately resamples the current workspace's windows.
Pin state survives config reloads in `$XDG_RUNTIME_DIR/noctalia-bar.force-show`.
`.local/bin/noctalia-bar-apply` serializes changes, sets only the local
`bar.default.reserve_space` override, disables runtime auto-hide, then sends
`bar-show`/`bar-hide` after the settings reload. Queued jobs read the newest desired
state, preventing stale rapid toggles. The wallpaper layer allows shell discovery
when the hidden bar has no layer, including after a compositor reload.
Outside manual refreshes, only visibility/reservation changes or a new shell process
send IPC. Behavior follows
the focused workspace globally, not independently per
monitor. The bar remains visible until the shell is discovered at startup.

**Unresolved workspace/widget delay — experimental patch retained:** the user
reported a blank windows/workspaces section for about eight seconds after showing
the bar, or until a window/workspace event. The helper calls `hyprctl eval` after
`bar-show` to re-announce the active workspace's unchanged name with
`hl.dsp.workspace.rename`, triggering Noctalia's snapshot handler. It runs under
the existing serialization lock, skips missing/unnamed workspaces, and adds no
polling or background process. Local captures looked promising, but the user
reproduced the failure; those captures and mocked IPC tests did not establish a
reliable fix. The patch was briefly reverted, then restored at the user's request.
Earlier pin/unpin behavior and shared visibility/reservation IPC refresh remain
unchanged. Reservation-triggered widget reconstruction is a possible contributor,
not a confirmed root cause; the rendering delay remains unresolved.

Version/dependency checks found Noctalia **5.4.1**, Hyprland **0.57.2**, and Wayland
client **1.26.0**; all 97 runtime RPM requirements resolved, shared libraries loaded,
and `rpm -V noctalia` was clean. Cached Fedora metadata offered the installed
versions, and [upstream's latest release](https://github.com/noctalia-dev/noctalia/releases/latest)
was also 5.4.1. No package upgrades/downgrades were made. Related reports
[#1436](https://github.com/noctalia-dev/noctalia/issues/1436) (stale occupied state)
and [#3254](https://github.com/noctalia-dev/noctalia/issues/3254) (missing persistent
workspaces after reload) are not exact matches for the reported delay.

Mako still owns notifications, the existing level helpers retain perceptual
brightness and 5% volume steps capped at **150%** (including media keys).
Noctalia audio overdrive also permits 150% in its native controls. Notification
text shows the boosted percentage while its progress hint stays within 0–100.
Hypridle owns locking, Noctalia owns launching and screenshots, and tuned-ppd owns
power profiles.
Noctalia notification/OSD daemons,
idle/lock actions, dock, clipboard history, plugins, weather, app-theme templates,
and the optional blurred overview backdrop are disabled. NetworkManager is not
required: Noctalia also supports the existing standalone iwd backend.

Deliberate visual differences: native workspace labels/glyphs and brightness's
hardware-percentage label need not exactly match Waybar's rewritten labels and
perceptual percentage. Scroll/key adjustments still use the original helpers.

## Launcher and screen capture

- **Super+D** toggles `noctalia msg panel-toggle launcher`.
- **Super+A** starts `noctalia msg screenshot-region`; drag to capture, Esc cancels.
- **Super+Shift+A** runs `noctalia msg screenshot-fullscreen all`, preserving the
  previous all-output capture behavior rather than only the focused monitor.

`[shell.screenshot]` saves PNGs in `/home/chihin/Pictures/Screenshots` and copies
captures to the clipboard without an annotation/confirmation step or external
command. Change this absolute path for another account. Filename patterns use
strftime and omit the extension. For ad-hoc CLI overrides, put options **before**
the positional `all` target.

Live checks verified the launcher panel opens/closes, decoded a 2560×1600
full-screen PNG, completed a region drag yielding a decoded 320×224 PNG, and
verified the saved full-screen image was also copied as a readable clipboard PNG.
Rofi was removed with DNF autoremove disabled; Fuzzel and Slurp were already absent.
The obsolete Rofi/Fuzzel configuration and `mac-screenshot` helper were removed
from source and deployment manifests; repository-owned home symlinks were backed
up under `~/.local/state/asahi-rice/backups/noctalia-capture-20261112/`.
**Grim must remain installed**: Fedora's `xdg-desktop-portal-hyprland` requires it,
even though these Noctalia bindings no longer use it. `wl-clipboard` also remains.

## Deploy and validate

`setup/link-home.sh` deploys the configuration files and bar helper through the normal
file-by-file manifest. On a machine previously running Waybar, disable its old
startup owner explicitly (removing a manifest entry alone does not do this):

```sh
systemctl --user disable waybar.service
```

This does not stop a running bar. Prefer the next logout/login for a live Waybar
cutover; do not kill desktop UI processes just to reload their configuration.
Also stop/disable the old `random-wallpaper.timer` and `swaybg-wallpaper.service`
before migrating the helpers. Retire only verified repository-owned home symlinks
for legacy entries removed from `setup/home-files.txt`; linking is additive and
will not remove them automatically. In particular, the historical swaybg unit has
`Restart=always`: never run it with the new one-shot IPC compatibility helper.

The live cleanup removed `waybar`, `swaybg`, `pavucontrol`, `wiremix`, `wofi`, and
`blueman` with DNF dependency cleanup disabled, Cargo-installed `impala`, and the
standalone `~/.local/bin/bluetuith`. Waypaper and ironbar were already absent.
The package manifest no longer installs the obsolete frontends. User configuration,
wallpaper libraries, and shared desktop backends were preserved; `waybar-level`
remains actively used by Noctalia and the media keys. Retired deployment symlinks
are backed up under `~/.local/state/asahi-rice/backups/legacy-ui-20261112-110025/`.

Noctalia merges configuration-directory TOML first, then applies overrides from
`~/.local/state/noctalia/settings.toml`. Preserve that file and unrelated avatar,
wallpaper, and lockscreen state; reconcile only conflicting settings. Its theme
source/custom palette must be `custom`/`Waybar` for the fixed palette to apply.

**Important:** disabling previously applied app templates runs their undo hooks:
these can delete generated theme files and remove includes from application config.
Back up *all* affected outputs, config files, and template bookkeeping before doing
this on another machine. The initial migration backup is under
`~/.local/state/asahi-rice/backups/noctalia-20261111-125017/`. Existing generated
assets were recovered with offline `noctalia theme --render` using the old wallpaper
palette, without re-enabling live hooks. The recovered Hyprland theme module and
preserved tracked app configurations were verified against baseline SHA-256 hashes.
The obsolete generated `require("noctalia").apply_theme()` hook is no longer loaded.

```sh
python3 -m unittest discover -s tests
luac -p .config/hypr/noctalia-shell.lua
noctalia config validate
noctalia msg config-reload
hyprctl reload config-only
hyprctl configerrors
```

Read validation output as well as the exit status: unknown-key warnings may not
produce a failure exit status. Reload Noctalia before Hyprland so the controller
reconciles its runtime mode after shell configuration reloads. New mocked tests in
`tests/test_noctalia_setup.py` never manipulate the live desktop.

Manually check floating-only versus tiled workspaces, no top-edge reveal, Super+B/Super+X,
special workspaces, network/Bluetooth/audio popups, wallpaper selection, media
keys, and suspend/resume. Wallpaper automation logs its selections in
`~/.cache/noctalia/noctalia.log`; a background `noctalia-wallpaper` layer confirms
rendering is active. Suspend/resume and visual fidelity require interactive checks.

## Roll back without deleting configuration

1. Reinstall Waybar and whichever old network/Bluetooth/audio frontends you want,
   and deliberately restore their configuration/controller/helper deployment
   entries from Git or the backup. In `hyprland.lua`, restore `require("waybar")`
   instead of `require("noctalia-shell")`; restore the Super+B callback to
   `ToggleWaybarVisibility` in `keybindings.lua`.
2. Replace `hl.exec_cmd("noctalia")` in `autostart.lua` with
   `hl.exec_cmd("systemctl --user start waybar.service")`.
3. Restore `waybar.service` in `setup/user-services.txt`, then run
   `systemctl --user enable waybar.service` (without `--now`).
4. Prefer retaining Noctalia wallpaper ownership. If also rolling that back,
   reinstall swaybg and restore the old renderer scripts/units from Git history
   before disabling Noctalia wallpaper automation/rendering. The current
   `random-wallpaper.sh` sends Noctalia IPC and cannot serve the old restarting unit.
   Never run both renderers.
5. Log out and back in. Noctalia files and the existing state backup can remain.
   Restoring old settings wholesale may re-enable app-theme hooks; do so only when
   deliberately restoring that previous behavior.
