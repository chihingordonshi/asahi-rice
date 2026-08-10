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

## Status

Staged, not deployed. Nothing here has been installed into a real `.config` on any
machine.

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

To verify: diff any file here against the same path in `dot-files` at the commit above —
they should be byte-identical copies, not rewrites.
