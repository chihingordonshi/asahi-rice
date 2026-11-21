# Touch Bar notifications

Codex and interactive Pi completions share `codex-touchbar.service`. It alternates
silent, non-looping train/vines animations and skips events received while playback
is active. Selection persists across restarts; stale events are discarded.

## Client setup

The user-level Codex configuration needs this top-level setting, adjusted for the
account path:

```toml
notify = ["/home/chihin/.local/bin/codex-touchbar-notify"]
```

Restart Codex after changing it. The notifier accepts `agent-turn-complete` and
atomically writes an event under `~/.local/state/codex-touchbar/`; it neither
controls the display nor invokes privileged commands.

Pi's `.pi/agent/extensions/touchbar-notify.ts` is linked by `setup/link-home.sh`.
Run `/reload` or restart Pi after linking. It notifies on `agent_settled`, after
retries, compaction and queued continuations. Print/JSON/RPC sessions and subagents
are silent. Only session/leaf IDs are sent, never prompt or response text; delivery
is bounded to two seconds.

## Player and permissions

`.local/bin/touchbar` borrows the DRM panel from `tiny-dfr` and restores normal
controls on exit, errors and shutdown. It discovers the connected 60×2008 DSI panel
rather than assuming a DRM card number. Current read/write access to its device is
required, normally through the `video` group and a fresh login.

`setup/install.sh` validates and installs `setup/codex-touchbar.sudoers` as
`/etc/sudoers.d/codex-touchbar` (root-owned, mode `0440`). Adjust its username before
replication. It grants only `systemctl stop tiny-dfr` and `systemctl start tiny-dfr`;
there is no privileged animation daemon and no need for wheel-wide passwordless
sudo. Both the player and service provide cleanup.

The player uses `.build/touchbar-mpv/mpv`, falling back to
`~/.local/src/mpv-touchbar/build/mpv`. `TOUCHBAR_MPV_BIN` can select another
stride-patched build. Stock mpv needs the narrow-panel fix in
`tools/mpv-touchbar-padding.patch` (for mpv 0.41.0).

After FFmpeg ABI changes, rebuild from an existing patched source tree:

```sh
tools/build-touchbar-mpv.sh [patched-source-directory]
```

The default source is `~/.local/src/mpv-touchbar`. The script verifies the patch,
leaves source unchanged, downloads nothing, and installs no system files. It needs
Meson/Ninja, a compiler, and FFmpeg/libplacebo/libass/libdrm/ALSA/PulseAudio development
dependencies. The player checks that mpv starts before stopping services.

## Assets and checks

The tracked train/vines clips are deterministic 2008×60, 30 fps, silent FFV1 assets.
Regenerate them with:

```sh
python3 tools/generate-codex-touchbar-animations.py
```

Tests do not require Touch Bar hardware:

```sh
python3 tests/test_touchbar.py
python3 tests/test_codex_touchbar.py
bun test tests/pi-touchbar.test.ts
```

For a looping demonstration, see the separate [KDE booth guide](kde-fair-booth.md).
