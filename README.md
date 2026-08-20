# asahi-rice

Config backup for Chi Hin's spare M1 MacBook running **Fedora Asahi Remix**, for
schoolday-only use (browser, notes, light writing). Not a full system dotfiles repo —
see `.config/agents/fedora-asahi-setup.md` for the reasoning behind the whole setup.

These files were originally curated from [dot-files](https://github.com/chihingordonshi/dot-files)
(the Arch/XPS16 rice), then adapted and extended for this machine specifically. They are
**live** — deployed to `$HOME` on the real M1 and kept in sync from it (see
`asahi-rice-sync` under "Status" below) — not just a staged reference anymore.

**New here?** Start with [Replicating this on your own M1](#replicating-this-on-your-own-m1)
— it's the one section written as a checklist rather than a log. Everything else below
is history, in roughly this order:

- [Replicating this on your own M1](#replicating-this-on-your-own-m1) — the checklist, start here
- [What's here and why](#whats-here-and-why) — per-path table, what each config dir is for
- [Deliberately left out](#deliberately-left-out) — things considered and skipped, and why
- [Decisions log](#decisions-log) — early build-out notes, chronological
- [Open question to revisit](#open-question-to-revisit--caelestia-may-no-longer-be-aarch64-dead) — one unresolved item
- [Critical finding — SDDM session picker](#critical-finding--log-in-via-hyprland-uwsm-managed-not-plain-hyprland) — read before your first login
- [Status](#status) — current sync mechanism, points at the latest dated entry per topic
- [Provenance](#provenance--exactly-what-was-done) — how this repo was built (agent-assisted, human-executed)
- Dated entries from `2026-08-10` onward — the actual build-out narrative, newest info wins where entries conflict

If you only read one thing before touching the M1: the "Critical finding" section on the
SDDM session picker. Getting that wrong silently breaks portals, polkit, and the keyring.

## Replicating this on your own M1

This repo is written as a running decision log (see "Decisions log" and the dated
sections below), not a turnkey installer — there's no `install.sh` here. To get an
equivalent setup on your own M1 running Fedora Asahi Remix, work through it in this
order, using the decisions log for the "why" and exact package/COPR names when a step
below is vague:

1. **Enable COPRs, then install packages.** (List verified against this machine's
   actual `rpm -q` / `dnf repoquery --installed` output, not reconstructed from memory.)
   - `lionheartp/Hyprland` COPR → `hyprland`, `hyprland-uwsm`, `hypridle`, `hyprlock`,
     `hyprpolkitagent`, `hyprsunset`, `kitty`, `qt6ct`, `waypaper`,
     `xdg-desktop-portal-hyprland` (plus their own deps — `hyprutils`, `hyprlang`,
     `hyprcursor`, `hyprgraphics`, `aquamarine`, etc. — `dnf` pulls those in
     automatically). The `technochip/Hyprland-aarch64` COPR named in
     `fedora-asahi-setup.md` is deprecated by its own maintainer — use
     `lionheartp/Hyprland` instead, see the 2026-08-10 decisions-log entry below.
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
     the 2026-08-10 "later still" decisions-log entry). Keep your own; it needs your
     own identity and credential-helper setup, not Chi Hin's.
4. **Verify the hardware-pinned values before trusting them, even on identical
   hardware.** `.config/hypr/monitors.lua` hardcodes `output = "eDP-1", mode =
   "2560x1600@60"` and `.config/hypr/input.lua` hardcodes `kb_layout = "us"` — both
   read from this specific machine via `hyprctl monitors -j` and `localectl status`,
   not guessed. Re-run those two commands on your own machine and adjust if anything
   differs (e.g. a non-US keyboard, or a different M1 panel variant).
5. **fcitx5 needs a first run before Pinyin actually works.** Installing the packages
   and having `~/.config/fcitx5/profile` in place isn't enough — fcitx5 has to
   actually launch once to generate its real profile state. See the 2026-08-10
   "waybar polish" decisions-log entry if Ctrl+Space doesn't switch input methods
   afterward.
6. **Log in via "Hyprland (uwsm-managed)" at the SDDM screen, not plain "Hyprland."**
   This is not optional — see "Critical finding" below for why plain Hyprland silently
   breaks portals, polkit, and the D-Bus secret-service keyring. `hyprland-uwsm` (from
   step 1) provides this session entry.
7. **Everything requiring `sudo` is on you.** COPR enablement and `dnf install` need to
   be run interactively — there's no scripted path here, by design (an agent helping
   with this has no route to a real root shell anyway, see "Provenance" below).

Optional extras that took real chasing on Chi Hin's machine and might not be worth
repeating on yours: the sticky-notes app (`org.x.sticky`, an unpackaged Fedora RPM
installed via `rpm -i --nodeps` plus two chased runtime deps — see the "App gaps
closed" decisions-log entry), and the shared exFAT partition between macOS and Fedora
(see "Shared data partition" below — destructive, only do this if you actually want
cross-OS file sharing and are comfortable resizing a live partition).

## What's here and why

| Path | Included because |
|---|---|
| `.config/hypr/hyprland.lua` | Copied verbatim from `dot-files` (Hyprland's autogenerated `require()` stub) |
| `.config/hypr/{monitors,programs,autostart,environment,permissions,appearance,animations,workspace-rules,layouts,misc,input,transparency,keybindings,window-rules}.lua` | The 14 files `hyprland.lua` requires — authored fresh, none existed in `dot-files` or anywhere else (verified by listing every `.lua` file in the repo) |
| `.config/hypr/scheme/`, `.config/hypr/hyprtoolkit.conf` | Copied from `dot-files` unchanged |
| `.config/kitty/` | Fallback/likely terminal |
| `.config/cava/` | Audio visualizer config + themes + shaders |
| `.config/btop/` | System monitor, cross-platform, no porting needed |
| `.config/neofetch/` | Lightweight, cross-platform |
| `.config/qt6ct/`, `.config/Kvantum/`, `.config/kdeglobals` | Qt/KDE theming, relevant if the KDE Plasma fallback DE is used instead of Hyprland |
| `.config/pavucontrol.ini` | Audio mixer settings |
| `.zshrc`, `.p10k.zsh` | Shell + prompt |
| `.config/agents/fedora-asahi-setup.md` | The research/decisions briefing this backup is staged against |
| `.config/hypr-quickmenu/` | Config for the hand-rolled HUD launcher (`.local/bin/hypr-quickmenu`) autostarted in `hypr/autostart.lua` |
| `.config/mako/` | Notification daemon, autostarted in `hypr/autostart.lua` |
| `.config/rofi/` | Launcher, bound to SUPER+D |
| `.config/waypaper/` | Wallpaper backend/folder selection, read by `random-wallpaper.service` and the waybar wallpaper-backend menu |

## Deliberately left out

- **`.config/caelestia/`** — Quickshell has a known unresolved aarch64-linux execution
  bug, so caelestia won't run on this machine. The setup notes say default to waybar or
  ironbar instead; neither has a config here yet.
- **`.config/obs-studio/`** — explicitly out of scope, this machine isn't for
  streaming/recording.
- **`.config/spicetify/`** — Spotify theming, rice extra not needed for the stated
  schoolday-only scope.
- **`.config/nix-darwin/`** — macOS-specific, irrelevant on Fedora.
- **Sweet-Purple icon theme** — cosmetic, skipped to keep this minimal per the "not a
  rice project" goal in the setup notes.

## Decisions log

- **2026-08-10 — Panel/bar: ironbar.** The setup notes left this open, defaulting toward
  waybar (safest) or ironbar (a bit more visual headroom, same "no Quickshell dependency"
  risk profile) over HyprPanel/Wayle (archived/unproven) or eww (build-it-yourself). Chi Hin
  chose **ironbar** over the waybar default.
- **2026-08-10 — Hyprland install path: `lionheartp/Hyprland` COPR, not
  `technochip/Hyprland-aarch64`.** The COPR named in the original setup notes turned out to
  be self-marked deprecated (its own description says so), pointing at
  `lionheartp/Hyprland` as the successor. Verified `lionheartp/Hyprland` has a
  `fedora-44-aarch64` chroot with a successful build 5 days before this check
  (hyprland 0.56.2-1, 2026-08-05) before recommending it.
- **2026-08-10 — ironbar install path: `victorvintorez/packages` COPR.** ironbar isn't in
  Fedora's main repos. This COPR has a `fedora-44-aarch64` chroot with a successful
  ironbar 0.19.0-1 build. Only one aarch64-capable COPR found for ironbar at check time —
  no alternative was compared.
- **2026-08-10 — `.config/ironbar/` rewritten against the real bundled docs.** The first
  draft (written before ironbar was actually installed) guessed at module names and CSS
  `#id` selectors and got several wrong — e.g. real CSS selectors are classes like
  `.clock`/`.battery`, not `#clock`/`#battery`. Once ironbar was installed,
  `/usr/share/doc/ironbar/docs/modules/*.md` gave the real schema, and
  `ironbar --validate-config` confirmed the rewrite is valid. Current bar (top position
  only, per Chi Hin's request): `clock` (time+date, center), `sys_info` (cpu/mem),
  `network_manager` (wifi), `keyboard` (layout indicator, needs the `input` group — see
  below), `battery` (power) — no workspaces/tray/volume, since none were asked for.
- **2026-08-10 — Hyprland config: Lua, not hyprlang `.conf`.** Hyprland 0.55+ deprecated
  hyprlang (`.conf`) in favor of Lua, dropping it within 1-2 releases; a first pass at this
  wrote a hand-rolled `hyprland.conf` (wrong call — flagged and corrected same day). The
  `dot-files` repo's own `hyprland.lua` is Hyprland's unfilled autogenerated stub: it
  `require()`s 14 files (`monitors`, `programs`, `autostart`, `environment`, `permissions`,
  `appearance`, `animations`, `workspace-rules`, `layouts`, `misc`, `input`,
  `transparency`, `keybindings`, `window-rules`) that never existed anywhere in the repo —
  confirmed by listing every `.lua` file in the repo tree, not by assumption. This means
  the XPS16 itself has never actually loaded a real Lua config either. The top-level
  `hyprland.lua` here is copied verbatim from `dot-files`; the 14 submodules were authored
  fresh (there was nothing to copy), using real API syntax pulled from
  `github.com/hyprwm/Hyprland/blob/main/example/hyprland.lua` (the canonical upstream
  example matching this exact installed version, fetched directly rather than guessed) and
  cross-checked against a second real-world Lua config
  (`github.com/fancypantalons/hyprland-config`). All 15 files pass a `luajit` syntax check
  (`loadfile()`, parse-only, doesn't require the `hl` global). **Not yet verified against a
  live Hyprland start** — `hyprctl reload` does not re-execute Lua config (confirmed
  empirically: reloading after a change left `general:border_size`/`col.active_border` at
  hardcoded defaults), because the Lua script registers one-shot `hl.on("hyprland.start",
  ...)` autostart hooks that shouldn't re-fire on every reload. Real verification needs a
  full session restart, which closes whatever terminal is running inside the session being
  restarted — left for Chi Hin to do on their own schedule.
- **2026-08-10 — Hardware values pinned, not left on auto-detect.** `monitors.lua` uses
  `output = "eDP-1", mode = "2560x1600@60", scale = 2` — read from `hyprctl monitors -j`
  on this machine, not guessed. `input.lua`'s `kb_layout = "us"` was cross-checked against
  `localectl status` (`X11 Layout: us`) rather than copied from the XPS16 side, since
  keymap is exactly the kind of value that shouldn't travel between machines.
- **2026-08-10 — Package gaps found by diffing against `.config/agents/xps16-pacman-packages.txt`.**
  That file in `dot-files` is a full `pacman -Q` dump from the XPS16, not a curated rice
  list — filtered it for desktop/session-relevant entries and cross-checked against what
  was already installed here. Real gaps installed as a result: `xdg-desktop-portal-hyprland`
  (screen sharing / file-picker portal — actually already present as a hyprland
  dependency, but explicitly verified rather than assumed), `hyprpolkitagent` (the
  Hyprland-ecosystem polkit agent — swapped in for a generic KDE one used in the first
  draft), `mako` (the XPS16's actual notification daemon per this same package list, not a
  guess), `network-manager-applet` (GUI to actually join new wifi networks — ironbar's
  `network_manager` module is status-only, no connect UI), `hyprsunset`. `wl-clipboard`,
  `brightnessctl`, `grim`, `slurp`, `playerctl` were checked and found already present as
  existing dependencies.
- **2026-08-10 — Session infrastructure gap: no D-Bus activation environment update, no
  keyring/secret-service daemon, no polkit GUI agent running by default under Hyprland.**
  This is almost certainly why `gh auth` broke partway through this session (D-Bus
  service-activated the KDE secret-service compat layer with a stale/incomplete
  environment, and no `kwalletd6` was actually running to back it) — confirmed via
  `ps aux` showing no keyring daemon and `busctl --user list` showing the secret-service
  D-Bus names as `(activatable)` only, never actually running. `gh auth login` ended up
  re-storing the token in a plain `~/.config/gh/hosts.yml` file instead of the keyring on
  retry, which sidesteps the problem going forward. `autostart.lua` now starts
  `dbus-update-activation-environment`, `kwalletd6`, and `hyprpolkitagent` on session
  start as a longer-term fix.

## Open question to revisit — caelestia may no longer be aarch64-dead

While checking COPRs for Hyprland/ironbar, found **`celestelove/caelestia`**, a COPR that
successfully built `caelestia-shell` (v2.3.0-1) for **`fedora-44-aarch64`** specifically.
The original setup notes ruled out caelestia entirely because of a documented
engine-level Quickshell aarch64-linux execution failure — a packaging build succeeding
doesn't prove that bug is actually fixed (build ≠ runs), but it's evidence worth
re-checking before treating "caelestia is a wall on this hardware" as still true. Not
acted on — the ironbar decision above stands unless Chi Hin wants to reopen it after
someone actually test-runs `caelestia-shell` from that COPR.

## Critical finding — log in via "Hyprland (uwsm-managed)", not plain "Hyprland"

2026-08-10, after first actually logging into the Hyprland session that was set up
earlier the same day: Chi Hin reported "not everything looks good." Verified with a real
screenshot (`grim`) rather than guessing — most things were fine (clock, cpu/mem, keyboard
layout, battery percentage all rendering correctly, colors/border/monitor scale all
confirmed live via `hyprctl getoption` matching the Lua config, and the Hyprland log
explicitly reads `[cfg] Using lua config found at /home/chihin/.config/hypr/hyprland.lua`
— it is genuinely running the Lua config, not falling back). Two real problems:

1. `icon_theme = "Papirus-Dark"` in ironbar's config was never verified installed — it
   wasn't (`rpm -qa | grep papirus` = nothing). Switched to `"Adwaita"`, which is
   installed and has the specific symbolic icons ironbar's default profiles use
   (confirmed by checking for `network-wireless-signal-good-symbolic.svg` etc. under
   `/usr/share/icons/Adwaita` directly, not assumed).
2. No wallpaper daemon was configured, so Hyprland was drawing its own built-in
   placeholder background. Installed `swaybg`, autostarted as a flat color
   (`#131317`, the scheme's background token) since no wallpaper image is tracked in
   this repo.

Neither of those alone explained everything, so the root cause was traced further:
`xdg-desktop-portal.service` was failing to start (`systemctl --user status` showed
"Dependency failed", because `graphical-session.target` was never reached for this
session — confirmed via `systemctl --user status graphical-session.target` showing it
last stopped when the earlier Plasma session ended, and attempting to start it manually
returns `Operation refused, unit graphical-session.target may be requested by dependency
only`). **Plain "Hyprland" launched directly by SDDM never triggers that systemd target
chain.** The fix isn't a config change — it's logging in via the **"Hyprland
(uwsm-managed)"** session entry instead (`hyprland-uwsm`, already installed as a
dependency earlier the same day but not yet actually selected at the login screen). UWSM
(`uwsm start -e -D Hyprland hyprland.desktop`) properly binds startup to
`graphical-session-pre.target` → `graphical-session.target`, which is what actually
activates portals, polkit, and D-Bus secret-service in the right order — this is almost
certainly also the real root cause of the `gh` keyring failure from earlier in the day,
not just an ironbar cosmetic issue. The manual `dbus-update-activation-environment` /
`kwalletd6` / `hyprpolkitagent` lines in `autostart.lua` are left in as a defensive
fallback, but the actual fix is the session picker, not those lines.

**Action needed from Chi Hin**: next logout, select "Hyprland (uwsm-managed)" at SDDM, not
plain "Hyprland".

## Status

Superseded by later entries below — kept as the original day-one snapshot, not current
state. In particular: the panel switched from ironbar to **waybar** the same day (see
the "real hypr config landed, panel switched to waybar" entry), so `~/.config/ironbar/`
no longer exists on the real machine or in this repo. As of the most recent dated entry
above, the full config (Lua hypr config, waybar, fonts, fcitx5, app set) is deployed,
logged into via a real `uwsm`-managed Hyprland session, and actively used day-to-day —
this repo is a live sync target (`asahi-rice-sync`), not a staged-but-undeployed backup.
For what's actually true right now, read the decisions log and dated sections
chronologically and trust the latest one on any given topic.

## Provenance — exactly what was done

1. Cloned `chihingordonshi/dot-files` to a scratch directory (not `$HOME`) at commit
   `871899f7e1a1b86485b250e440062a6a83e8ff52` (2026-08-10).
2. Copied the specific files/directories listed in the table above into this repo's
   working tree — a plain `cp -r`, no symlinks, nothing written to any real `~/.config`.
3. Deliberately left out the items listed under "Deliberately left out" above — those
   files still exist in `dot-files` untouched, just not duplicated here.
4. Wrote this README, committed everything in this repo, and pushed to
   `github.com/chihingordonshi/asahi-rice` (private).
5. Deleted the scratch clone of `dot-files` afterward — it was only used as a source to
   copy from, never used as, or symlinked into, this machine's actual `.config`.
6. 2026-08-10, same day: confirmed via `hostnamectl` that this session is running
   directly on the target Fedora Asahi Remix M1 (currently KDE Plasma, nothing from this
   rice installed yet). Checked package availability with `dnf5 info`/COPR API queries
   (read-only, no sudo) for hyprland, kitty, cava, btop, qt6ct, kvantum, kvantum-qt5,
   fastfetch, ironbar, and fonts. Installed **JetBrainsMono Nerd Font** directly to
   `~/.local/share/fonts` (user-level, no sudo needed) from the official
   `ryanoasis/nerd-fonts` GitHub release, then ran `fc-cache`. Wrote
   `~/.config/ironbar/config.toml` and `style.css` by hand (not copied from anywhere —
   caelestia never had an ironbar config to port) using the hex values already recorded
   in `.config/hypr/scheme/current.lua` and `.config/btop/themes/caelestia.theme` in this
   repo. Copied both new files into this repo under the same path. Everything requiring
   `sudo` (COPR enable, `dnf5 install`) was handed to Chi Hin to run interactively — this
   agent has no path to a root shell.

To verify: diff any file here against the same path in `dot-files` at the commit above —
they should be byte-identical copies, not rewrites.

## 2026-08-10 (later same day) — real hypr config landed, panel switched to waybar, more app gaps closed

`dot-files` commit `5dedba7` ("Track nvim/fish/niri/fuzzel/wireplumber/tide-island/zed
configs...") added real content to all 14 `.config/hypr/*.lua` submodules that were empty
when this repo was first built — Chi Hin's dotbackup-cron only tracks changes to already-
tracked files, so these existed on the XPS16 the whole time but were never pushed until
this commit. Everything in `.config/hypr/` here was rebuilt against that real content:

- `keybindings.lua`, `appearance.lua`, `animations.lua`, `layouts.lua`, `misc.lua`,
  `transparency.lua`, `permissions.lua`, `workspace-rules.lua`, `window-rules.lua` copied
  **verbatim** (checked each for hardware/app-specific refs first — none found beyond
  standard XF86 media keys, which are hardware-generic).
- `monitors.lua`, `input.lua` kept hardware-pinned to this machine (`eDP-1 2560x1600@60
  scale=2`, `kb_layout=us` confirmed via `localectl`) but adopted real preferences that
  aren't hardware-specific: `kb_options=caps:super`, `sensitivity=0.2`, `natural_scroll`,
  `disable_while_typing`, `tap_to_click=false`, 3-finger-swipe workspace gesture.
  `monitors.lua` also had to gain a `resize_monitor` global function (referenced by
  `keybindings.lua`'s SUPER+L bind) since copying keybindings.lua verbatim without it
  would break config load.
- `programs.lua` rewritten to match the real config's bare-global variable style
  (`terminal`/`fileManager`/`browser`, no `local`/`return`) since `keybindings.lua` and
  `autostart.lua` reference these as globals — my first-draft `programs.lua` used a
  `return {...}` module pattern that was silently incompatible and caused real config
  errors once the real `keybindings.lua` was copied over. `fileManager`/`browser`
  adapted to what's actually installed (`dolphin`/`firefox`, not `nautilus`/
  `google-chrome-stable`).
- `autostart.lua`: `caelestia shell -d` → `waybar` (see below), kept
  `nm-applet`/`hyprpolkitagent`/terminal/`fcitx5`, dropped `tide-island`/`wayvnc`/
  `mihomo-party` (not installed, matches how the real file already had some of these
  commented out), `safeeyes` commented out (not packaged for Fedora, no COPR/dnf path
  found). Kept the M1-specific `dbus-update-activation-environment`/`kwalletd6`/`swaybg`
  lines since those fix problems unique to this machine.
- `environment.lua`: adopted the real fcitx5 IME env vars (`XMODIFIERS`, `QT_IM_MODULE`,
  deliberately no `GTK_IM_MODULE` — same reasoning as the real config's comment about
  native Wayland GTK apps vs XWayland/Qt). Cursor stayed Adwaita — Bibata-Original-Ice
  isn't packaged for Fedora and no COPR was found.
- Asked before removing anything "too fancy" (custom animation curves/springs, blur/
  shadow/glow decoration) — answer was keep everything as copied, not simplified.

**Panel: switched from ironbar to waybar.** Same spec as before (clock+date, cpu/mem,
wifi, keyboard layout, battery, top position only) but rebuilt against waybar's real man
pages (`waybar-clock/cpu/memory/network/hyprland-language/battery(5)`), not guessed.
`.config/ironbar/` removed from this repo. cpu/memory formats are `cpu:{usage}%` /
`mem:{percentage}%` per request. Network module has `on-click: nm-connection-editor`.

**App gaps closed, each verified working, not just installed:**
- **Launcher**: `rofi` installed, bound to SUPER+D (was calling `caelestia shell drawers
  toggle launcher`, a no-op here).
- **Sticky notes**: the real config's SUPER+V bind calls a D-Bus method on `org.x.sticky`
  — identified as `linuxmint/sticky` (not in Fedora repos). Found via the
  `yselkowitz/xapps` COPR (`fedora-44-aarch64` build succeeded), but that RPM's spec has
  a naming bug (`Requires: python3-xapps-override`, singular — nothing provides that
  exact capability, the real package is `python3-xapps-overrides`, plural), so `dnf`
  refused it outright. Downloaded the RPM directly and installed with
  `rpm -i --nodeps`, then chased two genuinely real missing runtime deps one at a time
  (`gspell`, `python3-xapp`) until it actually launched and `NewNoteBlank` produced a
  real note on screen (confirmed via screenshot, not just "no error").
- **Chinese Pinyin input**: `fcitx5-chinese-addons` installed (the XPS16 package list
  showed `fcitx5-chinese-addons`/`fcitx5-pinyin-zhwiki`, base `fcitx5` alone isn't enough
  for CJK input). `fcitx5-pinyin-zhwiki` (an enhanced dictionary) isn't packaged for
  Fedora — base Pinyin still works without it.
- **`power-profiles-daemon`**: skipped — `tuned-ppd` (already installed as a transitive
  dependency earlier) provides the same `ppd-service` D-Bus interface and the two
  packages hard-conflict by design; installing it would just mean removing `tuned-ppd`
  for no functional gain.
- **`cloudflare-warp-bin`**: present on the XPS16 but not referenced by any of the real
  config files (not an autostart entry, no keybind) — flagged, not installed, since a VPN
  client is a bigger standalone decision than an app-launcher/notes-app gap.
- **Touch Bar**: `tiny-dfr` (the Asahi Touch Bar daemon) was already installed and
  running with defaults — it already fully supports a volume/brightness/media-keys
  layer, just not shown by default (`MediaLayerDefault = false`, so F1-F12 shows unless
  Fn is held). Wrote `/etc/tiny-dfr/config.toml` with `MediaLayerDefault = true` to flip
  that, restarted the service. Not something to touch in this repo (system-level, not
  user `$HOME` config).

## 2026-08-10 (later still) — deployed the rest of the app configs, caelestia-widget replacements on the bar

The `kitty`/`cava`/`btop`/`qt6ct`/`Kvantum`/`kdeglobals`/`pavucontrol.ini`/`.zshrc`/
`.p10k.zsh` files curated into this repo on day one were never actually deployed to this
machine's real `~/.config` — only `.config/hypr/` and the bar config had been. That's why
kitty had no transparency despite the real `background_opacity 0.4` being tracked here the
whole time. Re-cloned `dot-files` fresh (it had grown substantially since the first pull —
`fish`, `fuzzel`, `niri`, `nvim`, `wireplumber`, `zed`, systemd units, `.zsh_functions`
were all added in the meantime) and deployed everything non-hardware-specific:
`kitty`, `cava`, `neofetch`, `btop`, `qt6ct`, `Kvantum`, `wireplumber` (bluetooth
HFP-disable tweak), `fish`, `fuzzel`, `nvim`, `kdeglobals`, `pavucontrol.ini`, `.zshrc`,
`.p10k.zsh`, `.zsh_functions`. `.gitconfig` deliberately **not** deployed over the real
one — saved as `~/.gitconfig-dotfiles-reference` instead, since this machine's actual
`.gitconfig` has the `gh` credential-helper setup that fixes the auth issue from earlier
in the day, and blindly overwriting it would break that again. `niri`/`zed`/`tide-island`
configs skipped (different compositor / editor / caelestia-adjacent, not part of this
machine's stack).

**Caelestia-widget replacements**: caelestia normally provides quick-access
widgets for a bunch of things (force-kill unresponsive windows, bluetooth, lock screen,
wallpaper picker, proxy client, power profile, wifi settings, workspace overview) —
none of that exists here since caelestia isn't installed. Mapped each to a real tool and
put them as **clickable buttons directly on the waybar bar** (first attempt used
keybinds instead, per instruction that was wrong — undone, redone as bar buttons only):

| Caelestia widget | Bar button | Backing tool |
|---|---|---|
| Kill unresponsive window | `kill` | `hyprctl kill` (built into Hyprland, click-to-target) |
| Bluetooth | `bt` | `kcmshell6 kcm_bluetooth` (bluedevil, already installed) |
| Lock screen | `lock` | `hyprlock` (installed) |
| Wallpaper picker | `wallpaper` | `waypaper` (installed) |
| Proxy client | `proxy` | `/opt/clash-party/mihomo-party` (already installed) |
| Power profile | shows current profile, click to cycle | waybar's native `power-profiles-daemon` module, backed by `tuned-ppd` |
| Wifi settings | (already existed) | `nm-connection-editor` via the network module's `on-click` |

Icon glyphs deliberately avoided for these buttons and for the power-profile module
(plain text labels instead) — waybar's default power-profile icons need FontAwesome,
which isn't in this bar's `font-family` stack, and guessing icon setups has been wrong
twice already today (Papirus-Dark, `#id` CSS selectors). `workspace overview`
(caelestia's other widget) maps to the official `hyprexpo` Hyprland plugin, but that
needs a source compile via `hyprpm` — flagged as a separate, slower step, not done in
this batch. `safeeyes` and Cloudflare WARP remain flagged-not-installed from earlier.

## 2026-08-10 (evening) — mihomo scaling, kitty blur, wallpaper rotation, autolock, monitor-scale keybind, waybar icons

**Mihomo Party window scaling.** The caelestia-widget proxy button opens mihomo-party at
its natural (oversized-for-this-panel) Electron window size. Went looking for a Hyprland
window-rule "scale" mechanism first — grepped `/usr/share/hypr/stubs/hl.meta.lua`
exhaustively and confirmed the only `scale` fields anywhere are monitor scale, gesture-zoom
scale, and shadow scale; no per-window content-scale rule exists, confirmed a second way via
`strings` on the Hyprland binary itself. Tried `pseudo = true` (the real "tiled but natural
size" mechanism) with a `size` rule alongside it — hit a known upstream bug
(hyprwm/Hyprland#7690) where `size` has no effect once `pseudo` is set, confirmed empirically.
Removed the window rule entirely and solved it on the Electron side instead:
`--force-device-scale-factor=0.75`, applied both to the waybar `proxy` button's `on-click`
and via a user-level `.desktop` override at
`~/.local/share/applications/mihomo-party.desktop` (XDG user overrides win over
`/usr/share/applications/` without needing `update-desktop-database`).

**Kitty blur.** Wasn't rendering despite the real `background_opacity` config being
deployed correctly and the intentional `opaque = true` window rule for `class:terminal`
being unrelated to blur. Root cause: the wallpaper was a flat solid color, so blur had
nothing behind the window to visibly blur — not a config bug at all.

**Random wallpaper rotation.** `~/.local/bin/random-wallpaper.sh` (mirrors the dot-files
reference exactly) plus `random-wallpaper.service`/`.timer` (`OnBootSec=1min`,
`OnUnitActiveSec=30min`, matches the reference's cadence). Hit a real systemd trap: a
`Type=oneshot` service kills its entire cgroup on exit, so backgrounding swaybg with plain
`setsid ... & disown` inside the script silently didn't survive — `pgrep` showed no swaybg
process after the service exited cleanly. Fixed with
`systemd-run --user --collect --unit=swaybg-wallpaper -- swaybg -i "$pick" -m fill`, which
spins up an independent transient unit that outlives the oneshot parent's cgroup teardown.

**hypridle 15-minute autolock.** Installed from the same COPR already providing Hyprland.
First pass put the config at `~/.config/hypridle/hypridle.conf` (following the
mako/kitty-style per-app-directory convention) — wrong; hypridle actually searches
`~/.config/hypr/` alongside `hyprland.conf`. Moved it, service came up clean. This build's
`hyprctl dispatch` parses its argument as a Lua expression (confirmed against the machine's
own shipped `/usr/share/doc/hypridle/example.conf`), so the `after_sleep_cmd`/DPMS calls use
`hyprctl dispatch 'hl.dsp.dpms({action = "on"})'`, not the plain `dpms on/off` syntax from
generic hypridle docs. Autolock only, on purpose — no manual lock keybind or waybar button
was added; hypridle's 15-minute timeout is the sole way this machine locks now (the
caelestia-widget `lock` button from the earlier session was removed as part of this).

**Monitor-scale keybind**, iterated through several rounds of spec changes to land on:
1.6x is the panel's default/base scale (not 1x, not 2x — this took explicit correction
mid-session). `mainMod+L` toggles 1.6x↔1x, `mainMod+SHIFT+L` toggles 1.6x↔2x, both
independently relative to the 1.6x base, implemented as two small toggle functions in
`monitors.lua` referenced by name from `keybindings.lua`.

**Waybar**: moved `cpu`/`memory` to `modules-right`, removed the wallpaper-picker and lock
buttons (lock per the hypridle-only decision above; wallpaper picker had no remaining
purpose once the timer-driven rotation above shipped). Added real `pulseaudio` and
`backlight` modules (not custom scripts — both have built-in scroll-to-adjust, confirmed via
`waybar-pulseaudio(5)`/`waybar-backlight(5)`, no manual `wpctl`/`brightnessctl` wiring
needed) and replaced every module's plain-text/placeholder formatting with real Nerd Font
glyphs — verified against this machine's actual installed
`JetBrainsMonoNerdFontMono-Regular.ttf` cmap via `fc-query -f '%{charset}'` rather than
assumed from a generic cheatsheet (two initially-planned icons, skull for `kill` and shield
for `proxy`, turned out to be missing from this font's coverage and were swapped for
covered alternatives).

**Process note**: waybar must never be `pkill`'d to force a config reload — save the file
and let it be reloaded manually. `hyprctl reload` remains fine for Hyprland-owned Lua config
changes. Also: don't disruptively kill/relaunch apps the user has open on their live session
while testing config changes — edit and validate the file, then ask, rather than poking at
a window the user is actively watching.

**Also this session**: documented a shared exFAT partition idea (for files needed on both
the macOS and Fedora sides, given switching OS is always a cold reboot with no
suspend-and-swap) in `.config/agents/fedora-asahi-setup.md`'s macOS section — not built yet,
planned for the actual Asahi install/partition step. Worked out (but did not execute) a
partition-shrink procedure for freeing space on this already-installed machine's Fedora
`btrfs` partition, kept informational-only given the destructive/hard-to-reverse nature of
resizing a live root filesystem. Audited installed KDE apps against what's already been
ported from the XPS16 and proposed (not yet executed) removing `konsole`/`konsole-part` and
`plasma-systemmonitor` as genuinely redundant with kitty and btop; kept everything else,
including the `plasma-desktop`/`plasma-workspace` core, since the setup doc's own documented
fallback plan (if the Hyprland COPR ever breaks) depends on that core staying installed.
Also surfaced, as a side finding, that both screenshot keybinds
(`Print`→`mac-screenshot`, `CTRL+Print`→`screengrab`) are currently dead — neither binary
exists on disk despite `grim`/`slurp` being installed as the intended backend — so Spectacle
is, for now, the only actually-working screenshot tool on this machine and was excluded from
the KDE removal list on that basis.

**Revert**: the `--force-device-scale-factor=0.75` mihomo-party fix above turned out to be
unnecessary — the panel's actual base scale (1.6x, set earlier this same session) already
renders the window at a reasonable size on its own. Removed the flag from the waybar
`proxy` button's `on-click` and deleted the `~/.local/share/applications/mihomo-party.desktop`
user override entirely (confirmed the underlying `/usr/share/applications/mihomo-party.desktop`
has no flag, so removing the override fully restores default launch behavior). Left as a
recorded dead end rather than erased, since the investigation into why no Hyprland-side scale
mechanism exists is still accurate and reusable if this ever comes up again for a different app.

## 2026-08-10 (later still) — waybar polish, fcitx5 Pinyin actually turned on

Widened the icon-to-text gap on the right-side waybar modules (waybar's `format` is a
single text node, no separate icon/label CSS split — the fix is literally an extra
space character in each format string). Swapped the power-profile module's icons for
its own `{profile}` text string, per request — simpler than maintaining an icon map.
Moved `hyprland/language` to `modules-left`; it still shows Hyprland's own XKB layout
state, unchanged.

**fcitx5 Pinyin**: the env vars (`XMODIFIERS`/`QT_IM_MODULE`) and autostart entry were
already in place from an earlier session, but fcitx5 had never actually been run, so no
profile existed and it was only running a bare `keyboard-us` layer. Wrote
`~/.config/fcitx5/profile` enabling `keyboard-us` + `pinyin`, confirmed Cloud Pinyin
loads automatically (it's an optional dependency of the pinyin addon, already enabled by
default — checked via `fcitx5-diagnose`'s addon list rather than guessing at config
syntax) and explicitly pinned the trigger key with `~/.config/fcitx5/config`
(`[Hotkey]\nTriggerKeys=Control+space`) rather than relying on fcitx5's undocumented-here
default, even though it happens to match. `.config/fcitx5` added to
`asahi-rice-sync`'s `LIVE_PATHS` since this is a genuinely new top-level config path.

## 2026-08-11 — removed redundant KDE apps

Removed `konsole`, `konsole-part`, `plasma-systemmonitor` via `dnf remove` (proposed
in the earlier app-redundancy audit, executed after explicit go-ahead). kitty already
covers the terminal, and btop covers system monitoring — konsole and
plasma-systemmonitor were unused duplicates. `plasma-drkonqi` (KDE's crash-report
dialog) was pulled out too as an unused dependency of plasma-systemmonitor; no loss,
just the crash-report popup.

Also fixed fcitx5 Ctrl+Space not switching input methods: an earlier explicit
`~/.config/fcitx5/config` write (`TriggerKeys=Control+space`) used the wrong on-disk
format for a list-type option (fcitx5 stores lists as indexed sub-entries, not a flat
`key=value` line), so it silently parsed as an empty list and disabled the trigger —
overriding the compiled default, which already included Control+space and worked fine
before that write. Deleted the override; confirmed via
`busctl --user call org.fcitx.Fcitx5 /controller org.fcitx.Fcitx.Controller1 GetConfig`
that the live config reverted to the default three-key list.

## 2026-08-11 (later) — file manager confirmed, Okular removed

Confirmed the desktop is on Dolphin — nautilus was never installed, so no ambiguity there.
Checked calendar apps for redundancy (none found: only korganizer is installed, kalendar
isn't). Found real redundancy in PDF viewers: WPS 365 (installed earlier for the SAT camp
prep) had registered itself as the default `application/pdf` handler, leaving Okular
installed but unused. Removed Okular (+ okular-part/okular-libs and now-unused deps
djvulibre-libs, ebook-tools-libs, libspectre) per explicit go-ahead; WPS stays default
for PDFs.

## 2026-08-11 (later still) — executed the partition shrink, new shared exFAT drive

Went ahead with the previously-informational-only partition shrink, now with actual
target numbers: shrink the Fedora btrfs volume (`nvme0n1p6`, was 597GiB with only 24GiB
used) by 256GiB and turn that into a new exFAT partition shared between Fedora and
macOS. Live sector math at this disk's native 4096B sector size:

1. `btrfs filesystem resize` shrunk the mounted root+home btrfs filesystem online to
   340.56GiB first — has to happen before the partition table edit so the filesystem
   never extends past the partition's new boundary.
2. `parted resizepart` on the still-mounted `p6` refused non-interactively
   (`--script` correctly aborted on the "partition is in use" warning, zero changes
   written) — forced through with `yes | parted ---pretend-input-tty ... resizepart`
   after confirming this is standard/safe: it's a pure GPT metadata edit, not a write
   to filesystem data blocks, since the filesystem was already shrunk to fit. Needed a
   reboot afterward for the kernel to cleanly pick up the smaller live root partition
   size rather than trying to hot-reread it.
3. Created `p8` (256GiB) in the freed space. First attempt's start sector wasn't
   1MiB-aligned (parted wants the start divisible by 256 sectors at this sector size)
   — recomputed to the next aligned sector, second attempt succeeded clean.
4. Formatted `p8` exFAT (`exfatprogs`, already installed) labeled `SharedData`.
5. Mounted at `~/data` (moved from an initial `/mnt/shared`) via `/etc/fstab`, with
   explicit `uid=1000,gid=1000,umask=022` — exFAT has no native Unix permissions, so
   without these the kernel driver mounts it root-owned and unwritable by a normal
   user. `nofail` so a missing/failed device doesn't hang boot.

This is the shared-partition idea from the macOS setup notes, finally built rather
than just planned. `/etc/fstab` itself isn't tracked in this repo (system file, not
under `$HOME`) — only the decision and mount options are recorded here.

Also added a `wallpaper()` zsh function (`.zsh_functions`) as a manual trigger for the
existing `random-wallpaper.service`/`.timer` rotation — just calls
`~/.local/bin/random-wallpaper.sh` directly rather than duplicating its random-pick
logic, so it changes wallpaper on demand instead of waiting for the 30-minute timer.
