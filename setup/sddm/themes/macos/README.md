# macOS-inspired SDDM theme

An original Sonoma/Sequoia-inspired blue-hour login screen, without Apple assets
or branding. All SVG artwork and icons are included; no network access, KDE
modules, shaders, or blur effects are needed. Inter is used when installed,
otherwise Sans Serif.

## Requirements and deployment

- SDDM 0.21 with its Qt 6 greeter and `SddmComponents`.
- Qt Quick, Qt Quick Controls 2 (Basic style), and Qt SVG.
- The host SDDM configuration uses Bibata Original Classic cursors at size 24.
  Install the Xcursor theme as a root-owned copy in
  `/usr/share/icons/Bibata-Original-Classic/` before running the installer; see
  `setup/system-state.md`. Its Weston configuration enables libinput,
  tap-to-click, and tap-and-drag.
- Copy this whole directory to the **root-owned**
  `/usr/local/share/sddm/themes/macos/`. Configure SDDM separately with
  `ThemeDir=/usr/local/share/sddm/themes` and `Current=macos` in `[Theme]`.
  Do not point the system greeter at a user-writable Git checkout.

This directory does not install itself or change authentication, autologin,
sessions, or system services. The account is restored from
`userModel.lastUser` / `lastIndex`, falling back to the first available account.
There are no visible user/session pickers. `theme.conf` pins the session to
`/usr/share/wayland-sessions/hyprland-uwsm.desktop`, using SDDM's `file` role rather
than a session index or translated name. The host setup also seeds this path in
SDDM's `[Last]` state. If the configured session or all accounts are missing,
the theme shows an explanation and disables sign-in; it never falls back to
plain Hyprland.

## Interaction

- Enter in the password field or clicking/tapping the arrow submits through
  `sddm.login()`.
- Tab / Shift+Tab move only through sign-in and available power controls.
  Escape clears the password when the password field has focus.
- The saved account's real name appears above the password field, falling back
  to its account name. The generic avatar deliberately avoids depending on
  readable home directories or AccountsService image files.
- Caps Lock is indicated below the field. Failed authentication clears the
  password, returns focus, and permits another attempt. While authentication is
  pending, duplicate submissions and power actions are disabled. PAM information
  messages do not unlock the pending request.
- Sleep/restart/shutdown are only offered when SDDM reports the capability.
  Keyboard layout and authentication policy remain the host's responsibility;
  this is a standard SDDM password UI, not a custom MFA/password-change dialog.

`theme.conf` accepts Qt `clockFormat` and `dateFormat` patterns. For example,
`clockFormat=h:mm AP` selects a 12-hour clock. Day/month names use Qt's locale.
The composition adapts to small screens and Qt's normal high-DPI scaling.
`sessionFile` selects the exact session desktop-file path; this host must keep
`/usr/share/wayland-sessions/hyprland-uwsm.desktop` to start Hyprland through uwsm.

## Safe smoke test

Run without connecting to the active graphical display:

```sh
env -u QT_QPA_PLATFORMTHEME -u QT_IM_MODULE \
  QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
  timeout 6s sddm-greeter-qt6 --test-mode \
  --theme /absolute/path/to/setup/sddm/themes/macos
```

A timeout is expected for a running greeter. On Fedora, diagnostics can go to
`journalctl --user _PID=<greeter-pid> --no-pager` instead of stderr. A real visual
review in a separate headless compositor is recommended before enabling the
theme. Test mode uses SDDM's mock accounts/sessions, not the host's saved state.

All files here, including the original SVG artwork, are MIT-licensed; see
`LICENSE`.
