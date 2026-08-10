# asahi-rice

Config backup staged for a spare M1 MacBook running **Fedora Asahi Remix**, for
schoolday-only use (browser, notes, light writing). Not a full system dotfiles repo —
see `.config/agents/fedora-asahi-setup.md` for the reasoning behind the whole setup.

These files are curated from [dot-files](https://github.com/chihingordonshi/dot-files)
(the Arch/XPS16 rice) and copied here **as reference**, not symlinked or applied to any
live `$HOME`. Review before actually deploying anything on the M1.

## What's here and why

| Path | Included because |
|---|---|
| `.config/hypr/` | Hyprland is the decided compositor (pending COPR availability check) |
| `.config/kitty/` | Fallback/likely terminal |
| `.config/cava/` | Audio visualizer config + themes + shaders |
| `.config/btop/` | System monitor, cross-platform, no porting needed |
| `.config/neofetch/` | Lightweight, cross-platform |
| `.config/qt6ct/`, `.config/Kvantum/`, `.config/kdeglobals` | Qt/KDE theming, relevant if the KDE Plasma fallback DE is used instead of Hyprland |
| `.config/pavucontrol.ini` | Audio mixer settings |
| `.zshrc`, `.p10k.zsh` | Shell + prompt |
| `.config/agents/fedora-asahi-setup.md` | The research/decisions briefing this backup is staged against |
| `.config/ironbar/` | Hand-written (not ported from `dot-files` — caelestia never had an ironbar config), matched to the Material-You palette in `.config/hypr/scheme/current.lua` |

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
  chose **ironbar** over the waybar default. Initial `.config/ironbar/config.toml` +
  `style.css` written the same day — see table above. Untested against a live ironbar
  install; treat as a draft to verify, not a finished config.
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

## Open question to revisit — caelestia may no longer be aarch64-dead

While checking COPRs for Hyprland/ironbar, found **`celestelove/caelestia`**, a COPR that
successfully built `caelestia-shell` (v2.3.0-1) for **`fedora-44-aarch64`** specifically.
The original setup notes ruled out caelestia entirely because of a documented
engine-level Quickshell aarch64-linux execution failure — a packaging build succeeding
doesn't prove that bug is actually fixed (build ≠ runs), but it's evidence worth
re-checking before treating "caelestia is a wall on this hardware" as still true. Not
acted on — the ironbar decision above stands unless Chi Hin wants to reopen it after
someone actually test-runs `caelestia-shell` from that COPR.

## Status

Not deployed as a live desktop yet. `ironbar` config is staged both here and at
`~/.config/ironbar/` on the actual Fedora Asahi Remix machine (this machine — checked via
`hostnamectl`: Fedora Linux Asahi Remix 44, KDE Plasma edition, currently running the KDE
Plasma fallback session with Hyprland not yet installed). Package installation is
in progress; see Provenance below for exactly what's been run and what's pending sudo.

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
they should be byte-identical copies, not rewrites. For `.config/ironbar/`, there is no
comparison source; it's new, and should be checked against a real running ironbar
instance before being trusted.
