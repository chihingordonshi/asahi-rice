-- SPDX-License-Identifier: GPL-2.0-or-later
-- Approximate the measured macOS Sequoia 15.3.2 default mouse curve.
-- Data: INRIA/libpointing, commit 46b0e706ec4aa24334d0a91cf728ac751688e6cc,
-- pointing-echomouse/darwin-24/{config.dict,f4.dat}, GPL-2.0-or-later.
-- See docs/macos-mouse-acceleration.md and docs/licenses/GPL-2.0-or-later.txt.

-- This mouse has no MOUSE_DPI metadata: 1000 CPI is an assumption, not a reading.
-- Set this to the mouse's actual hardware DPI for physically calibrated motion.
local mouse_cpi = 1000
local speed_multiplier = 1.0

-- Match physical pointer travel on the current 2560px / 1.6-scale / 286mm panel.
local target_logical_ppi = (2560 / 1.6) * 25.4 / 286
local source_logical_ppi = 1728 * 25.4 / 344.245
local source_cpi = 400
local source_interval_ms = 1000 / 125

-- Measured output pixels for input deltas 0..127 at 125 Hz, slider position 4
-- (HIDMouseAcceleration 0.6875). Values are NOT acceleration multipliers.
local measured_pixels = {
    0, 0.230339, 0.464648, 0.885612,
    1.65208, 2.41855, 3.18105, 3.95944,
    4.73385, 5.50827, 6.28665, 7.06107,
    7.83945, 8.61387, 9.39225, 10.1667,
    10.9411, 11.7195, 12.4939, 13.2723,
    14.0467, 14.8211, 15.5995, 16.3739,
    17.1523, 17.9267, 18.987, 20.7781,
    22.5652, 24.3523, 26.1395, 27.9305,
    29.2305, 30.9883, 32.7461, 34.5078,
    36.2656, 38.0234, 39.7852, 41.543,
    43.3008, 45.0586, 46.8203, 48.5781,
    50.3359, 52.0938, 53.8555, 55.6133,
    57.3711, 59.1289, 60.8906, 62.6484,
    64.4062, 66.1641, 67.9258, 69.6836,
    71.4414, 73.1992, 74.9609, 76.7188,
    78.4766, 80.2344, 81.9961, 83.7539,
    85.5117, 87.2734, 89.0312, 90.7891,
    92.5469, 94.3086, 96.0664, 97.8242,
    99.2188, 99.957, 100.699, 101.438,
    102.176, 102.918, 103.656, 104.395,
    105.137, 105.875, 106.613, 107.355,
    108.094, 108.832, 109.574, 110.312,
    111.051, 111.793, 112.531, 113.273,
    114.012, 114.75, 115.492, 116.23,
    116.969, 117.711, 118.449, 119.188,
    119.93, 120.668, 121.406, 122.148,
    122.887, 123.625, 124.367, 125.105,
    125.844, 126.586, 127.324, 128.066,
    128.805, 129.543, 130.285, 131.023,
    131.762, 132.504, 133.242, 133.98,
    134.723, 135.461, 136.199, 136.941,
    137.68, 138.418, 139.16, 139.898,
}

-- libinput accepts at most 64 points: 63 output-linear samples spanning the
-- measured range, then one constant-gain tail point. This smooths sharp corners.
local intervals = 62
local last_index = #measured_pixels - 1
local source_step = last_index / intervals

-- libinput samples output speed against raw device counts/ms. Scaling the input
-- axis by CPI and the output axis by logical PPI preserves physical velocities.
local step = source_step * mouse_cpi / source_cpi / source_interval_ms
local output_scale = target_logical_ppi / source_logical_ppi
    * speed_multiplier / source_interval_ms

local profile = { "custom", string.format("%.9f", step) }
for sample = 0, intervals do
    local source_index = sample * source_step
    local lower = math.min(math.floor(source_index), last_index)
    local upper = math.min(lower + 1, last_index)
    local pixels = measured_pixels[lower + 1]
        + (measured_pixels[upper + 1] - measured_pixels[lower + 1])
        * (source_index - lower)
    profile[#profile + 1] = string.format("%.9f", pixels * output_scale)
end

-- libinput extrapolates its last segment. Put it on the ray through the origin
-- so the tail holds the last gain, as libpointing does beyond its measured range.
local tail_pixels = measured_pixels[#measured_pixels] * (intervals + 1) / intervals
profile[#profile + 1] = string.format("%.9f", tail_pixels * output_scale)

-- Do not change the built-in trackpad, scrolling, or other mice.
hl.device({
    name = "usb-gaming-mouse-1",
    accel_profile = table.concat(profile, " "),
})
