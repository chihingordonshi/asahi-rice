# Mouse acceleration

## Active configuration

`.config/hypr/input.lua` uses adaptive acceleration with sensitivity `0.3`.
**No custom macOS curve is enabled.** The tracked `mouse-acceleration.lua`
module is not loaded and is not a verified macOS 27 preset.

A calibrated external-mouse profile needs mouse-specific measurements, the target
macOS tracking-speed setting, and known mouse CPI. This machine's
`usb-gaming-mouse-1` has unknown CPI and display scale 1.6. Its built-in
`apple-spi-trackpad` is a separate device; trackpad data is not a mouse substitute.

## Evidence and limitations

[Omarchy-Mac PR #775][trackpad-pr] describes a macOS 27-derived profile for
**M2-and-later `apple-mtp-multi-touch` trackpads**, not external mice. The author
reports extracting M4 `HIDAccelCurves`, evaluating tracking speed 0.6875, and
fitting 64 points at 11 mm/s intervals with at most 7% relative error. Its assumed
resolution is 98 input units/mm at display scale 2, with separate scroll points.
These are the author's results, not independently verified measurements here;
the inspected revision was `db473c3fd85d4cd390de98839e44bfb30bccd7f3`.
It does not establish a calibrated profile for either device on this M1.

[Hyprland 0.57][hypr-devices] accepts per-device `hl.device()` settings and
`accel_profile = "custom <step> <points...>"`. [libinput][libinput] expects output
speeds sampled against raw device counts/ms, not gain multipliers. Custom profiles
are not DPI-normalized and ignore ordinary acceleration speed. The installed
libinput 1.32.0 accepts at most 64 points. Check trackpad scrolling separately.

## Disabled module and licensing

`.config/hypr/mouse-acceleration.lua` uses
[INRIA/libpointing's macOS 15.3.2 `darwin-24` dataset][dataset], assumes 1000 CPI,
and resamples output linearly. One low-speed transition has roughly 20% localized
error. **It is disabled and is not macOS 27 evidence.**

The imported data and derived module retain GPL-2.0-or-later attribution; see
[`licenses/GPL-2.0-or-later.txt`](licenses/GPL-2.0-or-later.txt).
Unrelated dotfiles are not relicensed.

## Checks

```sh
python3 tests/test_mouse_acceleration.py -v
luac -p .config/hypr/input.lua .config/hypr/mouse-acceleration.lua
```

After an intentional input change, use `hyprctl reload config-only` and inspect
`hyprctl configerrors`.

[trackpad-pr]: https://github.com/omacom/omarchy-mac/pull/775
[hypr-devices]: https://wiki.hypr.land/0.57.0/configuring/core/devices/
[libinput]: https://wayland.freedesktop.org/libinput/doc/latest/pointer-acceleration.html
[dataset]: https://github.com/INRIA/libpointing/tree/46b0e706ec4aa24334d0a91cf728ac751688e6cc/pointing-echomouse/darwin-24
