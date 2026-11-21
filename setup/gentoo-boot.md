# Gentoo boot and reboot helper

## One-shot reboot

`reboot-gentoo` lives in `~/.zsh_functions`. In an existing Zsh session:

```zsh
source ~/.zsh_functions
reboot-gentoo --dry-run
reboot-gentoo  # Ends the current session.
```

It selects Gentoo with `sudo asahi-bless --next --set-boot Gentoo --yes`,
verifies that `--next --get-boot` reports exactly `Gentoo`, then runs
`sudo systemctl reboot`. The permanent boot default is unchanged. Help and
dry-run make no changes; failed selection or verification prevents reboot.
If reboot fails, the one-shot target remains set. Cancel it with
`sudo asahi-bless --clear-next`.

## Gentoo EFI handoff

Gentoo's ESP is filesystem UUID `48F3-1101`, PARTUUID
`129b14c5-d2f3-449f-865d-aee5af4dcd5d`. Verify these identifiers before mounting;
Fedora's `/boot/efi` is a different partition.

- `EFI/BOOT/BOOTAA64.EFI` is a copy of Gentoo's `EFI/Gentoo/grubaa64.efi`.
  Keep both copies synchronized when updating Gentoo GRUB.
- Gentoo's root-level `ubootefi.var` uses BootOrder `0001,0000,0002,0003`.
  Boot0001 is the whole-disk fallback, which searches the selected installation's
  ESP first; Boot0000 explicitly loads Fedora. This ordering prevents Gentoo's
  U-Boot from choosing Fedora ahead of its own fallback loader.
- Gentoo GRUB selects Btrfs UUID `5a2b8914-4c4b-485b-a13e-7b940c4cffba`,
  root subvolume `@`.

The fallback loader, variable-store CRC/order, and GRUB configuration pass offline
checks. **An actual Gentoo boot still needs verification by rebooting.**

To undo the ESP changes, mount Gentoo's ESP writable, restore
`EFI/Gentoo/ubootefi.var.before-boot-fix-20261121` to the root-level
`ubootefi.var`, and remove the added `EFI/BOOT/BOOTAA64.EFI` copy. Flush writes
and unmount cleanly. Do not apply this to Fedora's ESP or alter Apple's permanent
boot selection.

See the [Asahi boot process](https://asahilinux.org/docs/alt/boot-process-guide/)
and [platform quirks](https://asahilinux.org/docs/platform/quirks/).

## Checks

These tests use mocks and never reboot or change boot state:

```sh
zsh -n .zsh_functions
python3 -m unittest discover -s tests -p 'test_reboot_gentoo.py' -v
```
