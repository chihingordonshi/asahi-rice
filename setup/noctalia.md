# Native Noctalia shell

The active shell is Fedora's native Noctalia with Hyprland 0.57 Lua integration,
not Quickshell. It owns the bar, launcher, control popups, screenshots and wallpapers.

## Configuration

| Path | Purpose |
| --- | --- |
| `.config/noctalia/config.toml` | Bar, widgets, native controls, capture and wallpaper settings |
| `.config/noctalia/palettes/Waybar.json` | Fixed dark/lavender palette; both variants use the same dark colors |
| `.config/hypr/noctalia-shell.lua` | Layer rules, workspace-dependent visibility, pin/unpin bindings |
| `.local/bin/noctalia-bar-apply` | Serialized visibility/reservation IPC |
| `.config/hypr/autostart.lua` | Starts Noctalia once at session startup |

Noctalia applies `~/.local/state/noctalia/settings.toml` overrides after the config
TOML. Preserve unrelated local avatar, wallpaper and lockscreen state; reconcile
only conflicting settings. The fixed palette uses theme source `custom` and custom
palette `Waybar`.

**Template caveat:** disabling previously applied app-theme templates runs undo
hooks that can delete generated files and remove application includes. Back up all
affected outputs, application configs and template bookkeeping before changing
these settings. The obsolete generated `require("noctalia").apply_theme()` hook
is not loaded; do not re-enable it as part of a routine reload.

## Bar behavior

The 36px bar stays visible on empty or floating-only workspaces and hides when the
focused workspace has a mapped, non-hidden tiled window. An active special
workspace takes precedence. This follows focus globally, not independently per
monitor. Top-edge reveal and native auto-hide are disabled.

Workspace events reconcile immediately; a compositor-native 200ms fallback timer
reads state without shell polling. **Super+X / Super+.** toggle pinned visibility.
Pinning reserves 36px above tiled windows; unpinning releases that gap and resamples
the current workspace. Pin state survives config reloads in
`$XDG_RUNTIME_DIR/noctalia-bar.force-show`. Shell animations are disabled.

`noctalia-bar-apply` serializes requests, applies the latest desired state, sets
only the local `bar.default.reserve_space` override, and sends `bar-show`/`bar-hide`
after settings reload. Outside manual refreshes, IPC runs only on changes or
shell discovery. The bar remains visible until startup discovery completes.

**Known issue:** the workspace/window widget can remain blank for about eight
seconds after showing, or until a window/workspace event. The helper re-announces
the active workspace's unchanged name through `hl.dsp.workspace.rename` as an
experimental snapshot refresh. This is **not a reliable fix**; the rendering delay
remains unresolved. Mocked IPC tests do not establish visual correctness.

## Controls and ownership

- **Super+D:** toggle the native launcher.
- **Super+A:** region capture; drag to select, Esc cancels.
- **Super+Shift+A:** capture all outputs.
- The wallpaper button, `wallpaper [connector]`, `random-wallpaper` and
  `random-wallpaper.sh` send native `wallpaper-random` IPC. Noctalia scans and
  renders the recursive library and rotates randomly every **900 seconds**.
- The keyboard button restarts IBus without resetting preferences or learned data;
  unfinished composition is discarded. Super+R switches English/Rime.
- Native popups manage network, Bluetooth and audio. Standalone iwd is supported;
  NetworkManager is not required.
- `waybar-level` remains the active media-key/scroll helper: perceptual brightness,
  5% volume steps, maximum 150%. Native audio overdrive also allows 150%.

Wallpaper and screenshot paths are account-specific absolute paths in
`config.toml`: `/home/chihin/Pictures/Wallpapers` and
`/home/chihin/Pictures/Screenshots`. Screenshots are PNGs, saved and copied to the
clipboard without confirmation. CLI capture options precede the positional `all`
target. Keep Grim installed for `xdg-desktop-portal-hyprland`, and keep `wl-clipboard`.

Mako owns notifications; hypridle/hyprlock own locking; tuned-ppd owns power
profiles. Noctalia's duplicate notification/OSD, idle/lock, dock, clipboard, weather,
plugins, app-theme templates and blurred overview backdrop are disabled.

## Deployment and checks

`setup/link-home.sh` deploys the shell config and helper. It does not remove old
links or disable old services. Do not run a competing bar or wallpaper renderer:
Waybar, `random-wallpaper.timer` and `swaybg-wallpaper.service` are not part of the
active deployment. In particular, the retained restarting swaybg unit cannot use
the current one-shot Noctalia IPC helper. Prefer logout/login for shell changes
rather than killing live UI processes.

```sh
python3 -m unittest discover -s tests -p 'test_noctalia*.py'
luac -p .config/hypr/noctalia-shell.lua
noctalia config validate
```

Read validation output as well as exit status; unknown keys may only warn. After
an intentional configuration change, reload Noctalia before Hyprland:

```sh
noctalia msg config-reload
hyprctl reload config-only
hyprctl configerrors
```

Manually check tiled/floating/special workspaces, no edge reveal, pin/unpin, control
popups, launcher, screenshots, wallpaper selection, media keys and suspend/resume.
Wallpaper selections are logged in `~/.cache/noctalia/noctalia.log`; a
`noctalia-wallpaper` layer indicates active rendering.

See the [upstream Hyprland guide](https://docs.noctalia.dev/noctalia/compositor-settings/hyprland/)
and [system configuration](system-state.md) for backend and deployment details.
