# Fedora Asahi setup on the spare M1 — briefing for whichever agent reads this

If you're an agent running on the spare M1 MacBook and found this file: you're looking at
the result of a research conversation that happened on Chi Hin's other machine (Dell XPS16,
Arch Linux) before this Mac was ever touched. This is background and decisions, not a script
to execute blindly — read it, then talk to Chi Hin before doing anything irreversible
(partitioning, reinstalling, running unreviewed COPR/AUR binaries as root).

**Before acting on anything below, re-verify it.** This was written in August 2026. Package
availability, COPR maintainer activity, and upstream project status (especially anything
Quickshell-related) all move fast. Treat every claim here as "true as of research time,
confirm before relying on it," not as current fact.

## The goal

A lightweight, reliable **schooltime-only** machine. Not a rice project, not a dev workstation,
not where ML training happens — that's the XPS16's job. This M1 needs to survive a school day:
browser (mostly Google Docs and friends), notes, light writing, occasional lockdown-browser exams.
Storage is not a constraint (512GB+ Mac). If a choice trades "more capable" for "more fragile,"
pick reliable.

## Decided, with reasoning

- **Distro: Fedora Asahi Remix, not Arch Linux ARM.** Asahi's own team moved away from Arch ARM
  as the flagship specifically because of ARM package maintenance problems, and partnered with
  Fedora because Fedora treats aarch64 as a first-class primary architecture. Arch ARM (and the
  community "Asahi Alarm" project) still exists and works, but it reproduces the exact
  "small volunteer base, no guarantees" risk this machine is supposed to avoid — just spread
  across the whole base system instead of one package. Familiar pacman/yay muscle memory was
  the case *for* Arch ARM; it lost anyway because this machine needs to just work.
- **Compositor: Hyprland**, not niri. Chi Hin already runs Hyprland (and niri, and COSMIC) on
  the XPS16 rice — Hyprland is the smaller config delta and matches the target workflow
  (fullscreen-per-workspace + swipe gestures, close to macOS Spaces). It is **not** in Fedora's
  official repos on any architecture. The only aarch64 path found was a single-maintainer COPR:
  `technochip/Hyprland-aarch64`. **Check whether that COPR is still alive and tracking current
  Hyprland/Fedora releases before committing to it.** If it's stale or broken, the documented
  fallback is KDE Plasma 6 (officially Asahi-tested spin) with the **Krohnkite** KWin script for
  dynamic tiling — Chi Hin already runs half the KDE PIM stack (Dolphin, Kalendar, Akonadi,
  Konsole, Kvantum) so this isn't a cold start either.
- **Shell/panel: intentionally left undetermined.** See below — do not default to caelestia.

## Explicitly open — figure this out at setup time, don't assume

**Shell/panel.** Chi Hin's daily driver on the XPS16 uses caelestia (a Quickshell-based shell
on Hyprland). That will very likely **not** work here: Quickshell has a documented aarch64-linux
execution failure (reported June 2025, unresolved as of the last check), and it's an
engine-level bug, not something caelestia's own code can route around — so pairing niri with
noctalia instead doesn't dodge it either, since noctalia is also Quickshell-based. Options
that don't share this dependency, roughly ranked by ambition:

- **HyprPanel** — closest visually/functionally to caelestia's ambition, but the project was
  **archived by its maintainer on 2026-04-27**; development supposedly moved to a successor
  called **Wayle**. Check Wayle's current maturity and whether it has any ARM track record
  before trusting it for anything.
- **eww** (Rust + GTK, compositor-agnostic) — solid aarch64 story via Rust's cross-arch
  toolchain, but it's a widget toolkit, not a finished shell. Recreating caelestia's look here
  means building it yourself in Yuck, not installing something ready-made.
- **ironbar** (Rust + GTK4) — modular, hot-reload CSS, scales from plain bar to fuller panel.
  Lower ambition than caelestia, low risk.
- **waybar** — the boring, safest option. Chi Hin's stated preference if nothing fancier pans
  out: "I don't really need a great shell but it's nice to have one."

Given the actual preference expressed, **default toward waybar or ironbar** unless there's a
specific reason to chase HyprPanel/Wayle or build something in eww. Don't spend a long session
trying to make caelestia itself work on aarch64 — treat the Quickshell bug as a wall until
proven otherwise.

**Prior art worth raiding before building from scratch:** a Hyprland desktop environment called
"Dusky" was ported specifically to Apple Silicon (Asahi/Arch ARM), and there's a GitHub
discussion on `basecamp/omarchy` about running Omarchy (a Hyprland-based rice framework) on
MacBooks. Both target Arch ARM rather than Fedora, so packages won't map directly, but they're
real evidence Hyprland-on-this-hardware is solved territory, and their configs/notes may save
real time even after retargeting to dnf/COPR.

## Known gaps — plan around these, don't try to fix them

- **Hardware video decode isn't wired up.** The AVD driver was at V4L2 groundwork, not VA-API,
  last checked. Expect Google Meet/Zoom to decode on CPU: more fan noise, faster battery drain
  on calls than you'd expect. Not worth chasing a fix; just budget for it.
- **Suspend is s2idle, not deep sleep.** Fine for normal lid-close during a school day. Do not
  trust it over a long idle (overnight, a weekend) — battery loss reports were still meaningfully
  worse than macOS's own sleep as of the last check. Shut down fully before exam mornings rather
  than relying on wake-from-suspend.
- **No AUR-shaped catch-all exists.** Map each package individually: Fedora repo → COPR →
  Flatpak → build from source, in that order of preference. There is no single tool that
  replaces `yay`'s role.
- **Steam/Wine/gaming and GPU-heavy ML (YOLOv8/Ultralytics training) are out of scope for this
  machine entirely** — don't try to make them work, that's not what this Mac is for.

## The macOS side

**First, check for `~/.config/agents/m4-macos-notes.md`.** It's the output of an inventory
pass run on Chi Hin's actual M4 daily-driver Mac (see `m4-audit-request.md` for what it
covers), and it reflects real lived-with choices, not research — treat it as higher-confidence
than anything below. In particular: **AeroSpace was suggested for the macOS window manager
based on research alone and Chi Hin reports it's "insanely buggy" in practice — do not
re-suggest it.** Let the M4 notes (or a fresh conversation with Chi Hin) determine the actual
window-management pick instead of guessing again.

Otherwise, keep this side minimal: just macOS itself, the lockdown-browser app, Ghostty, LibreOffice. The Asahi
installer reserves ~38GB of free space on the macOS volume automatically for its own updates;
with that plus the above, a macOS partition around **60–80GB** is comfortable without starving
Fedora. Switching OS is always a cold reboot through Apple's own native firmware picker — there
is no rEFInd/GRUB-style theming available, and no way to suspend one OS and wake into the other.

## Practical bootstrap notes

- Dotfiles are a **bare git repo**: `github.com/chihingordonshi/dot-files`, worktree = `$HOME`.
  Clone it bare (`git clone --bare <url> ~/.dotfiles`), restore the `config`/
  `status.showUntrackedFiles=no` settings, checkout into `$HOME`. Most text config (shell, nvim,
  kitty, git, hypr/niri configs) lands unmodified this way — no per-file porting needed.
- Secrets (SSH keys, GPG keys, password-store) travel over a trusted channel, **not** through
  that git repo.
- CLI dev tooling (rustup, go, uv, gh, julia, docker) all have native aarch64 Linux builds —
  install lazily as actually needed rather than restoring the full XPS16 toolchain, since the
  stated scope here is browser/notes-first.

## Full app-by-app audit (every `~/.config` entry, not just the earlier highlights)

**General rule: when something has awkward or no aarch64 support, check for a Fedora-preinstalled
or trivially-available equivalent that covers the same job before spending effort chasing a port
of the exact original app.** Only chase the original if the substitute genuinely can't do the job.
Concretely:

- **WPS Office / WPS PDF** — no ARM build on the international site; only the China-region site
  (`linux.wps.cn`) ships aarch64 packages, a different channel with its own update/telemetry
  behavior. Don't chase it. For documents, LibreOffice is already the plan. For PDFs specifically,
  use whatever Fedora's chosen desktop preinstalls — GNOME's Papers/Evince, or Okular if the
  Plasma fallback DE is in use — both fully native aarch64, zero setup.
- **Zoom desktop client** — genuinely no official Linux ARM64 build (5+ year open feature
  request, still unresolved). Don't install anything for this: use the browser-based Zoom web
  client, or Google Meet directly, given the browser is already this machine's primary tool.
- **WeChat (`.xwechat`)** — a real dead end, not just an awkward port. Community reports say it
  won't even install on ARM64 (ARM32 only), and the "unofficial clients" are rough Electron
  reimplementations of the protocol, not the real client. There is no preinstalled substitute
  here since it's a specific network, not a generic file format — either accept the browser-based
  WeChat web client's reduced feature set, or don't run WeChat on this machine and keep using it
  on the M4/XPS16.
- **OBS Studio** — not an official ARM64 target for the OBS team; distro-packaged ARM64 builds
  exist for Debian/Ubuntu, Fedora-specific status unconfirmed. Skip entirely — this machine is
  school-only, OBS was for the XPS16's streaming/recording setup, not coursework.
- **Docker Desktop** (the GUI app specifically, not the `docker` CLI/Engine, which is fine) —
  status unconfirmed for Linux aarch64. Low priority given this machine's scope; the CLI alone
  covers anything actually needed here.
- **Notion** — no official Linux app on any architecture, but the unofficial "Notion Electron"
  wrapper ships real aarch64 packages and is actively maintained, reportedly tested on Fedora
  specifically. Safe to use.
- **Warp terminal** — officially ships Linux ARM64 packages, but there are reported ARM64 crashes
  tied to GPU/Vulkan driver quirks on some systems. Worth test-launching before relying on it,
  given Asahi's Mesa/Vulkan stack is nonstandard. kitty (already the XPS16 default) or Ghostty
  are safer bets if Warp misbehaves.
- **clash-verge-rev / mihomo-party** (now renamed **clash-party** upstream) — both ship real
  aarch64 RPM/DEB builds directly. Non-issue.
- Everything else present — GIMP, Pinta, MuseScore, qalculate, mpv, vlc, audacious, cava,
  bongocat, chess-tui, safeeyes, screengrab, tigervnc, wayvnc, fcitx/fcitx5/ibus, VS Code, Zed —
  is mainstream FOSS or built on a toolchain (Rust, Go, Qt, GTK, .NET) with a solid aarch64
  Linux story. Not individually gap-checked beyond that; flag anything that actually breaks.

## What to do when you (the agent) actually read this

1. Confirm with Chi Hin that this is still the plan — dates above may be stale by the time
   you're reading this.
2. Re-check the specific unresolved items: `technochip/Hyprland-aarch64` COPR activity,
   Quickshell's aarch64 execution-failure issue status, Wayle's maturity.
3. Walk through disk partitioning and installation interactively — this is destructive and
   not something to run unattended.
4. Ask before anything not covered above rather than assuming continuity with the XPS16 setup.
