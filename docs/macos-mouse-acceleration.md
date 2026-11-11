# macOS-derived mouse acceleration on Hyprland 0.57

## What is implemented

`.config/hypr/input.lua` loads `mouse-acceleration.lua`, which calls
`hl.device()` for **`usb-gaming-mouse-1` only**. The built-in trackpad, global
sensitivity/profile, other mice, and scroll configuration are left alone.
No daemon, kernel module, package installation, or root access is needed.

The curve is based on **measured macOS Sequoia 15.3.2 data**, not the commonly
shared, unvalidated cubic "macOS-like" approximation. INRIA/libpointing's
`darwin-24/f4.dat` records the default fourth tracking-slider position
(`HIDMouseAcceleration = 0.6875`) using a 400-CPI reference input at 125 Hz.
Its 128 measurements are retained as source data, then resampled to 63 positions
plus one tail endpoint to fit libinput's 64-point limit.

This is an **approximation**, not a port of Apple's complete input pipeline.
Actual mouse CPI is unknown, and libinput's velocity estimation/interpolation,
polling, diagonal motion, and display layout can differ from macOS. It has not
been compared experimentally with the same physical mouse running macOS.

## Conversion, not just copying the numbers

[libinput custom profiles][libinput] take **output speed**, not gain multipliers,
at evenly spaced **raw device counts/ms**. Custom profiles do not normalize
mouse DPI, and ordinary `input.sensitivity` does not change their speed.

For source sample `P(i)`, assumed mouse CPI `D`, and logical display PPIs `L`:

```text
h         = 127 / 62
step      = h * D / (400 * 8)
points[k] = interpolate_output(P, k*h) / 8 * (L_target / L_source) * speed_multiplier
            for k = 0..62
gain(v)   = output_speed(v) / v
```

Output-space interpolation is linear. This is not libpointing's default
gain-space interpolator. The 64-point cap requires some smoothing: relative to
linear interpolation through all source outputs, error peaks at about **+19.9%**
at source index 3 (a sharp low-speed transition). It is below **1.9%** across
source indices 4–127; the measured endpoint is preserved exactly.

Eight milliseconds is the source's 125-Hz report interval. The recorded source
logical PPI is `1728 * 25.4 / 344.245 ≈ 127.50`. The current panel's logical PPI
is `(2560 / 1.6) * 25.4 / 286 ≈ 142.10`, using its resolution, scale and width.
These conversions aim to preserve **physical pointer travel**, rather than
blindly copying pixel/count values between screens and mouse resolutions.

The implementation explicitly **assumes 1000 CPI**, because this mouse's udev
metadata has no `MOUSE_DPI`. This is not an actual hardware measurement.
At that assumption, `step ≈ 0.640120968`; gain starts around `0.106`, reaches about
`0.614`, and ends near `0.491`. Declining high-speed gain is in the measured
source data; output speed itself remains increasing.

libinput extrapolates its final segment. The added sample is
`points[63] = points[62] * 63 / 62`, making that segment lie on a ray through the
origin. Above the measured range, gain therefore stays constant rather than
running away or decaying, matching libpointing's last-gain clamp.

## Tuning and rollback

Edit `.config/hypr/mouse-acceleration.lua`:

- **`mouse_cpi`**: set to the mouse's actual hardware DPI/CPI setting. This
  changes both the effective gain and the physical speeds at which it changes.
  A DPI-switch button can change this without updating udev metadata.
- **`speed_multiplier`**: starts at `1.0`. Increase for faster pointer travel
  without moving the acceleration thresholds; decrease for slower travel.
  Keep both values positive. The macOS default curve may feel slower than
  libinput adaptive acceleration.
- **`target_logical_ppi`**: update if the display resolution, scale, or physical
  dimensions change. One static curve cannot physically match every monitor in
  a mixed-DPI layout.

Apply this module alone, without replaying unrelated startup configuration:

```sh
hyprctl eval 'dofile(os.getenv("HOME") .. "/.config/hypr/mouse-acceleration.lua")'
```

For an immediate, temporary return to the previous adaptive profile:

```sh
hyprctl eval 'hl.device({ name = "usb-gaming-mouse-1", accel_profile = "adaptive" })'
```

For persistent rollback, remove `require("mouse-acceleration")` from `input.lua`
and reload the configuration. Other input settings need not change.

## Verification

```sh
python3 tests/test_mouse_acceleration.py -v
luac -p .config/hypr/input.lua .config/hypr/mouse-acceleration.lua
hyprctl configerrors
```

Tests check device isolation, Lua/LuaJIT compatibility, conversion anchors,
increasing output speed, measured gain bounds, constant-gain extrapolation,
and acceptance by the installed libinput C API without accessing input devices.
Successful live Lua evaluation verifies Hyprland accepts the configuration;
there is no claimed per-device effective-profile readback or subjective match.

## Sources and attribution

- [Hyprland 0.57 device configuration][hypr-devices]: `hl.device()` API.
- [Hyprland 0.57 input options][hypr-input]: `custom <step> <points...>` syntax.
- [libinput pointer acceleration][libinput] and [configuration API][libinput-api]:
  units, interpolation/extrapolation, DPI and sensitivity behavior. The installed
  libinput 1.32.0 API rejects more than 64 points; its [internal header][point-cap]
  also defines `LIBINPUT_ACCEL_NPOINTS_MAX = 64`.
- INRIA/libpointing, pinned commit
  `46b0e706ec4aa24334d0a91cf728ac751688e6cc`:
  [measurement metadata][metadata], [default curve][curve], and
  [interpolation implementation][interpolation]. Source `f4.dat` SHA-256:
  `a6378ee8c182cb406c3b27b0ae91d5afe9e430cb2180d2990e4001be445e2aa9`.

The imported measurement data and derived Lua module are **GPL-2.0-or-later**,
following [libpointing's license declaration][upstream-license]. A copy is in
[`licenses/GPL-2.0-or-later.txt`](licenses/GPL-2.0-or-later.txt). This notice does
not relicense unrelated dotfiles.

[hypr-devices]: https://wiki.hypr.land/0.57.0/configuring/core/devices/
[hypr-input]: https://wiki.hypr.land/0.57.0/configuring/core/config-options/
[libinput]: https://wayland.freedesktop.org/libinput/doc/latest/pointer-acceleration.html
[libinput-api]: https://wayland.freedesktop.org/libinput/doc/latest/api/group__config.html
[point-cap]: https://gitlab.freedesktop.org/libinput/libinput/-/blob/1.32.0/src/libinput-private.h
[metadata]: https://github.com/INRIA/libpointing/blob/46b0e706ec4aa24334d0a91cf728ac751688e6cc/pointing-echomouse/darwin-24/config.dict
[curve]: https://github.com/INRIA/libpointing/blob/46b0e706ec4aa24334d0a91cf728ac751688e6cc/pointing-echomouse/darwin-24/f4.dat
[interpolation]: https://github.com/INRIA/libpointing/blob/46b0e706ec4aa24334d0a91cf728ac751688e6cc/pointing/transferfunctions/Interpolation.cpp
[upstream-license]: https://github.com/INRIA/libpointing/blob/46b0e706ec4aa24334d0a91cf728ac751688e6cc/README.md
