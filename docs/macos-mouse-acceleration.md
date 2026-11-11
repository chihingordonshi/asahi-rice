# macOS mouse acceleration research — Hyprland 0.57

## Current status

**No custom macOS curve is enabled.** The automatic
`require("mouse-acceleration")` has been removed from `input.lua`, and the USB
mouse has been returned to adaptive acceleration. Existing sensitivity,
trackpad settings, and unrelated input edits are preserved.

The previous implementation used older measurements without evidence that they
represent macOS 27. That was not sufficient for the requested current behavior.
The historical module remains tracked for provenance, not as a recommended or
verified macOS 27 preset.

## Current macOS 27 evidence

[Omarchy-Mac PR #775][current-pr], created 2026-10-29 and updated 2026-11-09,
reports a macOS 27-derived libinput custom profile:

- The author extracted `HIDAccelCurves` from an M4 MacBook Pro and M4 MacBook Air,
  then evaluated IOHIDFamily's parametric acceleration at tracking speed 0.6875.
- Its 64 output-speed points are fitted at 11 mm/s intervals; the author reports
  at most 7% relative error and a same-machine comparison with macOS.
- It targets **`apple-mtp-multi-touch` built-in trackpads on M2 and later**, at
  98 input units/mm and display scale 2.
- It explicitly leaves external mice unchanged and configures `scroll_points`
  separately to preserve the trackpad's scrolling behavior.

These are the PR author's results, not independently verified measurements here.
The inspected PR head was `db473c3fd85d4cd390de98839e44bfb30bccd7f3`.

**This is not an external-mouse curve.** This system's USB device is
`usb-gaming-mouse-1`, its actual CPI is unknown, and display scale is 1.6. Its
built-in trackpad is also a different device, `apple-spi-trackpad`. Copying the
PR's numbers unchanged to either device would not establish a calibrated match.

No verified macOS 27 **external-mouse** dataset was found in the current search.
That does not prove that none exists, or that Apple changed or retained the old
curve. A defensible mouse implementation needs current mouse-specific curve
parameters or measurements, the target tracking-speed setting, and known mouse
CPI. Do not relabel older data or use a trackpad curve as a mouse substitute.

## Configuration checks and the reported failure

A real `hyprctl reload config-only` succeeded and `hyprctl configerrors` was
empty before the rollback. The reported configuration failure was therefore
**not reproduced**. An earlier deployment attempt did encounter a missing
module path before its live symlink was created, but that is only a possible
explanation for an earlier error, not a confirmed diagnosis of the user's report.
The exact error message or screenshot is needed if the failure persists.

The tests no longer assert the presence of unrelated mpv gesture listeners.
That assertion was brittle when the user disabled their mpv block; it was not
evidence of a mouse-profile configuration error.

```sh
python3 tests/test_mouse_acceleration.py -v
luac -p .config/hypr/input.lua .config/hypr/mouse-acceleration.lua
hyprctl reload config-only
hyprctl configerrors
```

## Relevant current interfaces

[Hyprland 0.57][hypr-devices] uses `hl.device()` for per-device settings and
`accel_profile = "custom <step> <points...>"` for custom motion curves.
[libinput][libinput] expects output speeds sampled against raw device counts/ms,
not gain multipliers. Custom profiles are not DPI-normalized and ignore the
ordinary acceleration-speed setting. The installed libinput 1.32.0 accepts at
most 64 points. Trackpad scrolling needs separate attention when selecting a
custom profile; it is not safe to assume that changing motion cannot affect it.

## Retained historical experiment and attribution

`.config/hypr/mouse-acceleration.lua` contains measurements from
[INRIA/libpointing's `darwin-24` dataset][historical], recorded on macOS 15.3.2,
at commit `46b0e706ec4aa24334d0a91cf728ac751688e6cc`. It assumes 1000 mouse CPI
and performs output-linear resampling, including a roughly 20% localized error
at one low-speed transition. **It is disabled and is not macOS 27 evidence.**

The imported data and derived module retain GPL-2.0-or-later attribution; see
[`licenses/GPL-2.0-or-later.txt`](licenses/GPL-2.0-or-later.txt). Unrelated
dotfiles are not relicensed.

[current-pr]: https://github.com/omacom/omarchy-mac/pull/775
[hypr-devices]: https://wiki.hypr.land/0.57.0/configuring/core/devices/
[libinput]: https://wayland.freedesktop.org/libinput/doc/latest/pointer-acceleration.html
[historical]: https://github.com/INRIA/libpointing/tree/46b0e706ec4aa24334d0a91cf728ac751688e6cc/pointing-echomouse/darwin-24
