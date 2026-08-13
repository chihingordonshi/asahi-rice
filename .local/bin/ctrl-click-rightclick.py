#!/usr/bin/env python3
# Remaps Ctrl+click on the trackpad into a right-click.
# Grabs the raw trackpad device exclusively and re-emits everything through a
# virtual device that mirrors its capabilities, so libinput/Hyprland see a
# device that behaves identically except for this one gesture. The keyboard
# is only read (never grabbed) to track Ctrl state -- normal typing and
# shortcuts are completely untouched.
#
# This device is a clickpad (INPUT_PROP_BUTTONPAD) using libinput's
# clickfinger click method, which *always* derives left/right/middle from
# simultaneous touch count and unconditionally drops any raw BTN_RIGHT it
# receives (real clickpad hardware can only ever report BTN_LEFT). So instead
# of substituting BTN_RIGHT, this spoofs a second touch contact at the same
# position as the real finger when Ctrl is held, letting libinput's own
# clickfinger logic derive BTN_RIGHT itself -- the same path a real 2-finger
# press already uses.
#
# Caveat: Ctrl is still physically held when the resulting right-click is
# delivered, so apps see "Ctrl+Right-click", not a bare right-click. Most
# apps treat context-menu clicks the same either way, but a few (terminals,
# browsers) bind extra behavior to Ctrl+click specifically -- watch for that.
#
# Safety: the exclusive grab on the trackpad is released automatically by the
# kernel the moment this process exits (crash, SIGTERM, Ctrl+C) -- the
# compositor's existing connection to the real device resumes immediately,
# no restart needed. The keyboard is never grabbed, so it's unaffected no
# matter what happens to this process.

import asyncio
import sys

import evdev
from evdev import ecodes

TRACKPAD_NAME = "Apple SPI Trackpad"
KEYBOARD_NAME = "Apple SPI Keyboard"
CTRL_KEYS = {ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL}

SYNTHETIC_SLOT = 15  # top of this device's 0-15 slot range; real touches won't reach it
SYNTHETIC_TRACKING_ID = 9999
SYNTHETIC_PRESSURE = 5000
# This device's libinput quirk (50-system-apple.quirks, "Apple Laptop Touchpad (SPI)
# applespi driver") sets AttrTouchSizeRange=150:130 and no AttrPressureRange at all --
# touch promotion out of TOUCH_HOVERING is gated by ABS_MT_TOUCH_MAJOR/MINOR crossing 150,
# not by ABS_MT_PRESSURE (confirmed via raw capture: real click-time pressure never exceeds
# ~150 out of a 0-6000 range, yet touches promote fine). AttrPalmSizeThreshold=1600, so stay
# well under that too. Values below mirror real click-time touch sizes observed on hardware.
SYNTHETIC_TOUCH_MAJOR = 400
SYNTHETIC_TOUCH_MINOR = 600
SYNTHETIC_WIDTH_MAJOR = 1800
SYNTHETIC_WIDTH_MINOR = 1600


def find_device(name):
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        if dev.name == name:
            return dev
    sys.exit(f"device '{name}' not found")


def make_virtual(src):
    caps = src.capabilities(absinfo=True)
    caps.pop(ecodes.EV_SYN, None)
    return evdev.UInput(
        events=caps,
        name=src.name + " (remapped)",
        vendor=src.info.vendor,
        product=src.info.product,
        version=src.info.version,
        bustype=src.info.bustype,
        input_props=src.input_props(),
    )


class State:
    ctrl_held = False
    spoofed_click = False
    current_real_slot = 0
    last_x = 0
    last_y = 0


async def watch_keyboard(kb):
    async for event in kb.async_read_loop():
        if event.type == ecodes.EV_KEY and event.code in CTRL_KEYS:
            if event.value == 1:
                State.ctrl_held = True
            elif event.value == 0:
                if not any(
                    k in kb.active_keys() for k in CTRL_KEYS if k != event.code
                ):
                    State.ctrl_held = False
            print(f"[kb] code={event.code} value={event.value} -> ctrl_held={State.ctrl_held}", flush=True)


def spoof_touch_start(ui):
    # This device's touch/finger-count state is gated by the legacy
    # BTN_TOOL_FINGER/BTN_TOOL_DOUBLETAP protocol, not by ABS_MT_PRESSURE --
    # confirmed via raw evdev capture of a real 2-finger press, where a second
    # touch landing flips BTN_TOOL_FINGER 1->0 and BTN_TOOL_DOUBLETAP 0->1 in
    # the same frame. Without mirroring that, libinput's fake-finger sanity
    # check caps nfingers_down back down regardless of the MT slot data.
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_SLOT, SYNTHETIC_SLOT)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TRACKING_ID, SYNTHETIC_TRACKING_ID)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_POSITION_X, State.last_x)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_POSITION_Y, State.last_y)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_PRESSURE, SYNTHETIC_PRESSURE)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TOUCH_MAJOR, SYNTHETIC_TOUCH_MAJOR)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TOUCH_MINOR, SYNTHETIC_TOUCH_MINOR)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_WIDTH_MAJOR, SYNTHETIC_WIDTH_MAJOR)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_WIDTH_MINOR, SYNTHETIC_WIDTH_MINOR)
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_FINGER, 0)
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_DOUBLETAP, 1)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_SLOT, State.current_real_slot)
    ui.syn()


def spoof_touch_end(ui):
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_SLOT, SYNTHETIC_SLOT)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TRACKING_ID, -1)
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_FINGER, 1)
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_DOUBLETAP, 0)
    ui.write(ecodes.EV_ABS, ecodes.ABS_MT_SLOT, State.current_real_slot)
    ui.syn()


async def watch_trackpad(trackpad, ui):
    async for event in trackpad.async_read_loop():
        if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_MT_SLOT:
            State.current_real_slot = event.value
        elif event.type == ecodes.EV_ABS and event.code == ecodes.ABS_MT_POSITION_X:
            State.last_x = event.value
        elif event.type == ecodes.EV_ABS and event.code == ecodes.ABS_MT_POSITION_Y:
            State.last_y = event.value

        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_LEFT:
            if event.value == 1:
                State.spoofed_click = State.ctrl_held
                if State.spoofed_click:
                    spoof_touch_start(ui)
                    # Back-to-back syn() frames with no gap can land in the same
                    # kernel read batch libinput processes, making 2-finger
                    # recognition flaky. A short gap reliably forces separate
                    # frames; imperceptible to a human click.
                    await asyncio.sleep(0.02)
            print(f"[tp] BTN_LEFT value={event.value} ctrl_held={State.ctrl_held} spoofed_click={State.spoofed_click}", flush=True)
            ui.write_event(event)
            if event.value == 0 and State.spoofed_click:
                spoof_touch_end(ui)
                State.spoofed_click = False
            continue

        ui.write_event(event)


async def main():
    trackpad = find_device(TRACKPAD_NAME)
    keyboard = find_device(KEYBOARD_NAME)
    ui = make_virtual(trackpad)
    trackpad.grab()

    try:
        await asyncio.gather(
            watch_keyboard(keyboard),
            watch_trackpad(trackpad, ui),
        )
    finally:
        trackpad.ungrab()
        ui.close()


if __name__ == "__main__":
    asyncio.run(main())
