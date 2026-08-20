# asahi-rice

Config backup for Chi Hin's spare M1 MacBook running **Fedora Asahi Remix**, for
schoolday-only use (browser, notes, light writing). Not a full system dotfiles repo —
see `.config/agents/fedora-asahi-setup.md` for the reasoning behind the whole setup.

These files were originally curated from [dot-files](https://github.com/chihingordonshi/dot-files)
(the Arch/XPS16 rice), then adapted and extended for this machine specifically. They are
**live** — deployed to `$HOME` on the real M1 and kept in sync from it (see
`asahi-rice-sync` under "Status" below) — not just a staged reference anymore.

**New here?** Start with [Replicating this on your own M1](#replicating-this-on-your-own-m1)
— it's the one section written as a checklist rather than a log.

- [Replicating this on your own M1](#replicating-this-on-your-own-m1) — the checklist, start here
- [What's here and why](#whats-here-and-why) — every tracked path, one line each
- [Deliberately left out](#deliberately-left-out) — things considered and skipped, and why
- [Key decisions and gotchas](#key-decisions-and-gotchas) — grouped by topic, the "why" behind non-obvious choices
- [Open question to revisit](#open-question-to-revisit--caelestia-may-no-longer-be-aarch64-dead) — one unresolved item
- [Critical finding — SDDM session picker](#critical-finding--log-in-via-hyprland-uwsm-managed-not-plain-hyprland) — read before your first login
- [Status](#status) — what's live right now
- [Provenance](#provenance) — how this repo was built
- [Build history](#build-history) — condensed changelog, newest info wins over anything above

If you only read one thing before touching the M1: the "Critical finding" section on the
SDDM session picker. Getting that wrong silently breaks portals, polkit, and the keyring.

## Replicating this on your own M1

This repo isn't a turnkey installer — there's no `install.sh` here. To get an equivalent
setup on your own M1 running Fedora Asahi Remix, work through it in this order:

1. **Enable COPRs, then install packages.** (List verified against this machine's
   actual `rpm -q` / `dnf repoquery --installed` output, not reconstructed from memory.)
   - `lionheartp/Hyprland` COPR → `hyprland`, `hyprland-uwsm`, `hypridle`, `hyprlock`,
     `hyprpolkitagent`, `hyprsunset`, `kitty`, `qt6ct`, `waypaper`,
     `xdg-desktop-portal-hyprland` (plus their own deps — `hyprutils`, `hyprlang`,
     `hyprcursor`, `hyprgraphics`, `aquamarine`, etc. — `dnf` pulls those in
     automatically). The `technochip/Hyprland-aarch64` COPR named in
     `fedora-asahi-setup.md` is deprecated by its own maintainer — use
     `lionheartp/Hyprland` instead.
   - Fedora's main repos → `waybar`, `cava`, `btop`, `fastfetch`, `kvantum`,
     `kvantum-qt5`, `mako`, `rofi`, `swaybg`, `network-manager-applet`, `wl-clipboard`,
     `brightnessctl`, `grim`, `slurp`, `playerctl`, `fcitx5`, `fcitx5-chinese-addons`,
     `exfatprogs`, `gtk4-layer-shell`, `python3-gobject`, `python3-cairo` (the last
     three are for `hypr-quickmenu` and the Cairo clock in `autostart.lua` — both are
     Python/GTK4, and silently no-op at startup if these are missing).
   - `.config/neofetch/` exists in this repo but `neofetch` itself isn't installed here
     — `fastfetch` (`.config/fastfetch/`) is what's actually live; the neofetch config
     is a leftover from before the switch. Skip installing `neofetch` unless you want it.
   - `mpvpaper` — used by `waypaper` as the video-wallpaper backend (see
     `.config/waypaper/config.ini`, `waybar-wallpaper-backend*.sh`) — isn't packaged for
     Fedora and is installed to `/usr/local/bin/mpvpaper` here by building it manually
     (see [`mpvpaper`](https://github.com/GhostNaN/mpvpaper) upstream). Only needed if
     you want video wallpapers from `~/Videos/Wallpapers`; static-image wallpapers via
     `swaybg` work without it.
   - `dolphin` (file manager) and `firefox` (browser) — swap for your own picks if you
     want different ones; `programs.lua` (see below) needs to match whatever you choose.
   - Optional: the caelestia-widget replacements need `bluedevil` (for `kcmshell6
     kcm_bluetooth`) and whatever proxy client you use (Chi Hin's is
     `/opt/clash-party/mihomo-party`, installed separately, not via `dnf`).
   - Skip anything under "Deliberately left out" below unless you specifically want it.
2. **Install the font.** JetBrains Mono Nerd Font, from the official
   [`ryanoasis/nerd-fonts`](https://github.com/ryanoasis/nerd-fonts) GitHub release, unzipped
   into `~/.local/share/fonts`, then `fc-cache`. Everything here (waybar, kitty, the
   Cairo clock) assumes this exact font is present.
3. **Copy the config files into `$HOME`.** Every path under `.config/`, `.local/bin/`,
   `.local/share/applications/`, `Pictures/Wallpapers/`, plus the top-level dotfiles
   (`.zshrc`, `.p10k.zsh`, `.zsh_functions`) in this repo maps 1:1 onto the same path
   under your own `$HOME`. Plain `cp -r`, no symlinking needed (that's how this repo
   itself is kept in sync — see `.local/bin/asahi-rice-sync`).
   - `.local/bin/` specifically is a grab-bag, not all of it Hyprland config — the
     scripts actually referenced by the Hypr/waybar config are `hypr-quickmenu`,
     `hypr-overview`, `hypr-workspace-watch`, `mac-screenshot`,
     `wallpaper-auto-downscale`, `waypaper-set-backend.sh`, and the `waybar-*.sh`
     helpers (`waybar-cpu.sh`, `waybar-memory.sh`, `waybar-bluetooth.sh`,
     `waybar-fcitx5.sh`, `waybar-power-profile*.sh`, `waybar-wallpaper-backend*.sh`).
     Everything else in there is unrelated CLI tooling that got swept in by
     `asahi-rice-sync`'s blanket `.local/bin` entry — copy it too if you want it, skip
     it if you're only after the rice.
   - **Do not copy `.config/systemd/user/asahi-rice-sync.{service,timer}`, or enable
     them.** That unit pushes to `github.com/chihingordonshi/asahi-rice` — it's Chi
     Hin's repo sync, not a general-purpose tool, and you don't have push access to it
     anyway. Everything else under `.config/systemd/user/` (`hypridle.service`,
     `random-wallpaper.{service,timer}`, `swaybg-wallpaper.service`) is
     machine-generic and safe to bring over — enable with `systemctl --user enable
     --now hypridle.service random-wallpaper.timer`.
   - **Do not copy `.gitconfig`** (it isn't tracked here for exactly this reason — see
     "Key decisions and gotchas" below). Keep your own; it needs your own identity and
     credential-helper setup, not Chi Hin's.
4. **Verify the hardware-pinned values before trusting them, even on identical
   hardware.** `.config/hypr/monitors.lua` hardcodes `output = "eDP-1", mode =
   "2560x1600@60", scale = 1.6` and `.config/hypr/input.lua` hardcodes `kb_layout =
   "us"` — both read from this specific machine via `hyprctl monitors -j` and
   `localectl status`, not guessed. Re-run those two commands on your own machine and
   adjust if anything differs (e.g. a non-US keyboard, or a different M1 panel
   variant).
5. **fcitx5 needs a first run before Pinyin actually works.** Installing the packages
   and having `~/.config/fcitx5/profile` in place isn't enough — fcitx5 has to
   actually launch once to generate its real profile state. See "Key decisions and
   gotchas" below if Ctrl+Space doesn't switch input methods afterward.
6. **Log in via "Hyprland (uwsm-managed)" at the SDDM screen, not plain "Hyprland."**
   This is not optional — see "Critical finding" below for why plain Hyprland silently
   breaks portals, polkit, and the D-Bus secret-service keyring. `hyprland-uwsm` (from
   step 1) provides this session entry.
7. **Everything requiring `sudo` is on you.** COPR enablement and `dnf install` need to
   be run interactively — there's no scripted path here, by design (see "Provenance"
   below).
   - Optional convenience: put your user in `wheel` with passwordless sudo, so you're
     not typing your password for every `dnf`/`copr` command in step 1 —
     `sudo usermod -aG wheel <you>`, then in `sudo visudo` add (or uncomment)
     `%wheel  ALL=(ALL)  NOPASSWD: ALL`. This is fine for a personal single-user
     laptop like this one; it's a real security tradeoff (any process running as your
     user can now get root with no prompt) and not something to do on a shared or
     work machine.

Optional extras that took real chasing on Chi Hin's machine and might not be worth
repeating on yours: the sticky-notes app (`org.x.sticky`, an unpackaged Fedora RPM
installed via `rpm -i --nodeps` plus two chased runtime deps — see "Key decisions and
gotchas" below), and a shared exFAT partition between macOS and Fedora (destructive,
only do this if you actually want cross-OS file sharing and are comfortable resizing a
live partition — see "Build history" below for what that involved).

## What's here and why

| Path | What it is |
|---|---|
| `.config/hypr/` | Hyprland config, in Lua (not hyprlang `.conf` — see "Key decisions"). `hyprland.lua` is the autogenerated `require()` stub; the 14 files it requires (`monitors`, `programs`, `autostart`, `environment`, `permissions`, `appearance`, `animations`, `workspace-rules`, `layouts`, `misc`, `input`, `transparency`, `keybindings`, `window-rules`) are hand-authored |
| `.config/hypr/scheme/`, `.config/hypr/hyprtoolkit.conf` | Color scheme + Hyprland toolkit config, copied from `dot-files` unchanged |
| `.config/hypr-quickmenu/` | Config for the hand-rolled HUD launcher (`.local/bin/hypr-quickmenu`), autostarted |
| `.config/waybar/` | Status bar — clock, cpu/mem, network, battery, keyboard layout, plus the caelestia-widget replacement buttons (see "Key decisions") |
| `.config/waypaper/` | Wallpaper backend/folder picker, used by `random-wallpaper.service` and waybar's wallpaper-backend menu |
| `.config/mako/` | Notification daemon |
| `.config/rofi/` | App launcher, bound to SUPER+D |
| `.config/fuzzel/` | App launcher, alternate to rofi |
| `.config/fcitx5/` | Chinese Pinyin input method — needs a first real launch to generate `profile`, see replication step 5 |
| `.config/kitty/` | Terminal |
| `.config/fish/` | Alternate shell config (`.zshrc` is the default) |
| `.config/nvim/` | Neovim config |
| `.config/cava/` | Audio visualizer config + themes + shaders |
| `.config/btop/` | System monitor |
| `.config/fastfetch/` | System-info banner — the currently-used one (see "neofetch" note below) |
| `.config/neofetch/` | Superseded by fastfetch; kept as a leftover, not actively used |
| `.config/wireplumber/` | Audio routing tweak (disables Bluetooth HFP) |
| `.config/qt6ct/`, `.config/Kvantum/`, `.config/kdeglobals` | Qt/KDE theming, relevant if the KDE Plasma fallback is used instead of Hyprland |
| `.config/pavucontrol.ini` | Audio mixer settings |
| `.config/autostart/` | XDG autostart entries |
| `.config/systemd/user/` | User systemd units — `hypridle`, `random-wallpaper`, `swaybg-wallpaper` are machine-generic; `asahi-rice-sync` is Chi Hin-specific, do not copy (see replication step 3) |
| `.config/agents/fedora-asahi-setup.md` | The original research/decisions briefing this whole setup is built from |
| `.local/bin/` | Scripts the config actually references, plus unrelated CLI tools swept in by the sync script — see replication step 3 for which is which |
| `.local/share/applications/` | Desktop-entry overrides (e.g. Electron app launch flags) |
| `Pictures/Wallpapers/` | Images for the wallpaper rotation timer |
| `.zshrc`, `.p10k.zsh`, `.zsh_functions` | Shell, prompt, and a couple of manual-trigger helper functions |

## Deliberately left out

- **`.config/caelestia/`** — Quickshell has a known unresolved aarch64-linux execution
  bug, so caelestia won't run on this machine; waybar replaced it (see "What's here and
  why"). One aarch64 COPR build has since appeared — worth re-testing, see "Open
  question to revisit" below.
- **`.config/obs-studio/`** — explicitly out of scope, this machine isn't for
  streaming/recording.
- **`.config/spicetify/`** — Spotify theming, rice extra not needed for the stated
  schoolday-only scope.
- **`.config/nix-darwin/`** — macOS-specific, irrelevant on Fedora.
- **Sweet-Purple icon theme** — cosmetic, skipped to keep this minimal per the "not a
  rice project" goal in the setup notes.

## Key decisions and gotchas

**Package sources.** The Hyprland stack (`hyprland`, `hyprland-uwsm`, `hypridle`,
`hyprlock`, `hyprpolkitagent`, `hyprsunset`, `kitty`, `qt6ct`, `waypaper`,
`xdg-desktop-portal-hyprland`) comes from the `lionheartp/Hyprland` COPR, not
`technochip/Hyprland-aarch64` (deprecated by its own maintainer). The panel is
**waybar** — ironbar was the first pick (via a separate COPR) but was fully replaced
the same day; nothing named `ironbar` should exist anywhere in this repo.

**Hyprland config is Lua, not hyprlang `.conf`.** Hyprland 0.55+ deprecated `.conf` in
favor of Lua. `hyprland.lua` is the autogenerated stub that `require()`s 14 submodules;
all 14 were authored fresh against the upstream example config
(`hyprwm/Hyprland/blob/main/example/hyprland.lua`) for this exact installed version.
`hyprctl reload` does **not** re-execute Lua config — changes need a full session
restart to take effect, since the Lua registers one-shot `hl.on("hyprland.start", ...)`
autostart hooks that shouldn't re-fire on every reload.

**`hypridle` config location.** Goes in `~/.config/hypr/hypridle.conf`, not
`~/.config/hypridle/` (unlike most other apps' per-app-directory convention). This
build's `hyprctl dispatch` parses its argument as a Lua expression, so DPMS calls need
`hyprctl dispatch 'hl.dsp.dpms({action = "on"})'`, not the plain `dpms on/off` syntax in
generic hypridle docs. Autolock is 15 minutes, no manual lock keybind — hypridle's
timeout is the sole way this machine locks.

**Wallpaper rotation and systemd.** `random-wallpaper.service` is `Type=oneshot`, which
kills its whole cgroup on exit — backgrounding `swaybg` with `setsid ... & disown`
inside the script doesn't survive that. Fixed by spawning it as an independent
transient unit: `systemd-run --user --collect --unit=swaybg-wallpaper -- swaybg -i
"$pick" -m fill`.

**fcitx5.** `TriggerKeys` is a list-type option — a flat `key=value` line in
`~/.config/fcitx5/config` silently parses as empty and disables the trigger. Don't
hand-edit it; the compiled default (which already includes Ctrl+Space) is correct. Only
`~/.config/fcitx5/profile` (enabling `keyboard-us` + `pinyin`) needs to exist, and only
after fcitx5 has actually been launched once — see replication step 5.

**Icon theme.** `Papirus-Dark` isn't installed on this machine; bar configs use
`Adwaita` instead, which does have the specific symbolic icons the default module
profiles reference. Icon glyphs on the caelestia-widget waybar buttons and the
power-profile module are plain text, not icons — waybar's default icon set needs
FontAwesome, which isn't in this bar's font stack.

**Never `pkill` a live UI process (waybar, etc.) to force a config reload.** Save the
file and let it pick up the change on its own; killing/relaunching mid-session is
disruptive. `hyprctl reload` remains fine for Hyprland-owned Lua config changes.

**`.gitconfig` is never tracked here.** This machine's real `.gitconfig` has the `gh`
credential-helper setup that fixes the D-Bus/keyring auth issue described in "Critical
finding" below — overwriting it with a copied one would break that again.

**caelestia-widget replacements**, mapped onto real tools and added as waybar buttons
(caelestia's quick-access widgets don't exist without caelestia installed):

| Caelestia widget | Backing tool |
|---|---|
| Kill unresponsive window | `hyprctl kill` |
| Bluetooth | `kcmshell6 kcm_bluetooth` (bluedevil) |
| Wallpaper picker | `waypaper` |
| Proxy client | `/opt/clash-party/mihomo-party` |
| Power profile | waybar's native `power-profiles-daemon` module (backed by `tuned-ppd`) |
| Wifi settings | network module's `on-click` → `nm-connection-editor` |
| Lock screen | not on the bar — superseded by hypridle's 15-minute autolock |
| Workspace overview | not done — needs the `hyprexpo` plugin compiled via `hyprpm`, flagged as a future step |

**Left un-replicated on purpose:** `power-profiles-daemon` (conflicts with `tuned-ppd`,
which already provides the same D-Bus interface), `cloudflare-warp-bin` (present on the
XPS16 but not referenced by any config here), `safeeyes` (not packaged for Fedora).
Sticky notes (`org.x.sticky`, real package `linuxmint/sticky` via the `yselkowitz/xapps`
COPR) needed `rpm -i --nodeps` due to a naming bug in that COPR's spec
(`python3-xapps-override` vs. the real `python3-xapps-overrides`), plus two chased
runtime deps (`gspell`, `python3-xapp`).

## Open question to revisit — caelestia may no longer be aarch64-dead

While checking COPRs for Hyprland/ironbar, found **`celestelove/caelestia`**, a COPR that
successfully built `caelestia-shell` (v2.3.0-1) for **`fedora-44-aarch64`** specifically.
The original setup notes ruled out caelestia entirely because of a documented
engine-level Quickshell aarch64-linux execution failure — a packaging build succeeding
doesn't prove that bug is actually fixed (build ≠ runs), but it's evidence worth
re-checking before treating "caelestia is a wall on this hardware" as still true. Not
acted on — the waybar setup stands unless Chi Hin wants to reopen it after someone
actually test-runs `caelestia-shell` from that COPR.

## Critical finding — log in via "Hyprland (uwsm-managed)", not plain "Hyprland"

Logging into plain "Hyprland" at the SDDM screen never reaches
`graphical-session.target`, so portals, polkit, and the D-Bus secret-service keyring
never activate. That's what caused a broken `gh auth` keyring, a missing wallpaper
daemon (Hyprland was drawing its own placeholder background — fixed by adding
`swaybg`), and other session-level breakage that initially looked like separate config
bugs but weren't.

**The fix is the session picker, not a config change.** At SDDM, select **"Hyprland
(uwsm-managed)"**, not plain "Hyprland". `uwsm start -e -D Hyprland hyprland.desktop`
properly binds startup to `graphical-session-pre.target` → `graphical-session.target`,
which is what actually activates portals, polkit, and D-Bus secret-service in the right
order. The manual `dbus-update-activation-environment`/`kwalletd6`/`hyprpolkitagent`
lines in `autostart.lua` are left in as a defensive fallback, but aren't the real fix.

## Status

This repo is a live sync target, not a staged reference: `asahi-rice-sync` mirrors the
real `$HOME` into this repo and pushes automatically once a day (see
`.local/bin/asahi-rice-sync`). The full config — Lua Hyprland config, waybar, fonts,
fcitx5, app set — is deployed and in daily use via a real `uwsm`-managed Hyprland
session.

## Provenance

Built by an AI coding agent (Claude Code) working from
`.config/agents/fedora-asahi-setup.md`, with Chi Hin running anything requiring `sudo`
or interactive confirmation — the agent never had a root shell. Source material is
[dot-files](https://github.com/chihingordonshi/dot-files) (the Arch/XPS16 rice): files
were copied as-is where hardware-independent, rewritten where machine-specific (monitor
and keyboard values, package availability), or authored fresh where nothing existed to
copy from (the 14 Hyprland Lua submodules). Package installs, COPR enablement, and the
exFAT partition work (see "Build history" below) were all run interactively by Chi Hin.

## Build history

Condensed changelog — see git log for exact diffs, and the sections above for anything
still relevant to replicating or maintaining this setup.

- **2026-08-10** — Initial build: Hyprland (Lua config), ironbar panel, core app set,
  JetBrains Mono Nerd Font.
- **2026-08-10 (later)** — Real Hyprland config landed once `dot-files` got proper
  content pushed for the first time; panel switched ironbar → waybar; app gaps closed
  (rofi launcher, sticky notes, Pinyin input packages, touch bar media-key default).
- **2026-08-10 (later still)** — Remaining app configs (kitty, cava, btop, qt6ct,
  Kvantum, wireplumber, fish, nvim, etc.) actually deployed to `$HOME` — day one had
  only staged them in the repo. caelestia-widget replacements added to waybar.
- **2026-08-10 (evening)** — Wallpaper rotation timer, hypridle autolock, monitor-scale
  keybind (1.6x base, toggles to 1x/2x), waybar icon pass, KDE app redundancy audited.
- **2026-08-11** — Removed redundant KDE apps (konsole, plasma-systemmonitor, Okular —
  kitty/btop/WPS 365 cover the same ground). Fixed a fcitx5 trigger-key regression.
- **2026-08-11 (later)** — Executed the Fedora/macOS shared exFAT partition: shrank the
  Fedora btrfs root by 256GiB, created and formatted a new exFAT partition, mounted at
  `~/data` with `uid=1000,gid=1000,umask=022` (exFAT has no native Unix permissions) and
  `nofail` in `/etc/fstab`. Added a `wallpaper()` zsh function as a manual trigger for
  the rotation timer.
