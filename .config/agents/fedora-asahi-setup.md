# Fedora Asahi setup context

This M1 MacBook runs Fedora Asahi Remix with a UWSM-managed Hyprland session and
native Noctalia shell. The goal is a reliable, lightweight daily machine for
browser work, notes and writing.

## Source of truth

- [README](../../README.md): current desktop, setup checklist and documentation.
- [`setup/`](../../setup/): package/repository/service manifests and deployment scripts.
- [System configuration](../../setup/system-state.md): root-owned configuration,
  machine-specific networking, shared storage and recovery.
- [Noctalia](../../setup/noctalia.md): active shell behavior and known limitations.

Hyprland uses Lua configuration and the `lionheartp/Hyprland` COPR. Noctalia is
the native Fedora package, not the Quickshell implementation. Waybar and Fcitx
files in the tree are inactive; deploy only `setup/home-files.txt`. IBus + Rime
handle input. SDDM must start **Hyprland (uwsm-managed)**.

## Constraints

- Verify hardware names, absolute paths, package availability and account-specific
  settings before reusing this setup elsewhere. Do not treat retained configs as
  evidence that an application or service is active.
- Home files are symlinked into this checkout; system files are root-owned copies,
  never symlinks into the user-owned worktree.
- Keep credentials, learned input data, browser profiles and local media out of Git.
- Partitioning and OS installation require explicit review; the shared exFAT volume
  is already configured and is not a bootstrap step.
- macOS remains available for applications that require it. Switching OS ends the
  current session; Linux suspend does not hand off to macOS.
- Prefer available aarch64 packages and reliable substitutes over speculative ports.
  Gaming and GPU-heavy ML are not setup goals. Recheck hardware support before
  making performance or battery-life claims.
