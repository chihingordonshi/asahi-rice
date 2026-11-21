# Gentoo boot handoff and reboot helper

## Repair on 2026-11-21

Selecting Gentoo in Apple's boot picker started Gentoo's m1n1/U-Boot, but
U-Boot loaded Fedora's EFI loader. This was **not** GRUB detecting another OS.

Evidence collected while Fedora was running:

- `/proc/device-tree/chosen/asahi,efi-system-partition` named Gentoo's ESP
  PARTUUID `129b14c5-d2f3-449f-865d-aee5af4dcd5d` (filesystem UUID `48F3-1101`,
  currently `/dev/nvme0n1p9`). The actual GRUB loader reported Fedora's ESP.
- Gentoo's ESP had `EFI/Gentoo/grubaa64.efi`, but no
  `EFI/BOOT/BOOTAA64.EFI` fallback loader.
- Gentoo's `ubootefi.var` stored BootOrder `0000,0001,0002,0003`. Boot0000
  explicitly loaded Fedora's `\EFI\fedora\shimaa64.efi`; Boot0001 was the
  whole-disk `nvme 0` fallback.
- Gentoo's GRUB configuration correctly selected Btrfs UUID
  `5a2b8914-4c4b-485b-a13e-7b940c4cffba`, root subvolume `@`, and the existing
  `7.2.14-p1-asahi-dist` kernel/initramfs. `grub2-script-check` passed.

Only Gentoo's ESP was changed:

1. Copied its existing `EFI/Gentoo/grubaa64.efi` to
   `EFI/BOOT/BOOTAA64.EFI`.
2. Backed up its original variable store to
   `EFI/Gentoo/ubootefi.var.before-boot-fix-20261121`.
3. Reordered its stored BootOrder to `0001,0000,0002,0003`, preserving every
   Boot entry, PlatformLang, and SbatLevel. This puts the selected installation's
   fallback ahead of Fedora's explicit entry, retaining Fedora as a fallback.

The installed U-Boot source archive in Gentoo,
`/var/cache/distfiles/u-boot-2026.04_p1.tar.gz`, confirms this behavior:
`lib/efi_loader/efi_bootmgr.c` searches the selected system ESP first for a
whole-disk fallback; `efi_var_file.c` reads the variable store from that ESP.
`include/efi_variable.h` defines its 24-byte little-endian `<QQII>` header;
CRC32 covers the bytes after the header. Only six bytes changed in the
976-byte store: four CRC bytes and the first two BootOrder values.

Verified SHA-256 values:

| File | SHA-256 |
| --- | --- |
| Both Gentoo GRUB EFI copies | `b69a24100ec5ef83c6fad71416010e6f2635f08f8434477a6fa4771e1241be27` |
| Original/backup variable store | `5f4473878a8dd16d77b6ad9c66fa9433ca13ef51c6acb6f3b727ccaf5541bc4b` |
| Repaired variable store | `9a9d33a4cc3c904a2293a2f007fc779be9443b38e7d9c6d3e8cb98576641c045` |

The fallback copy, variable-store CRC/order, and backup were checked after
installation and after remounting read-only. Fedora's files, live EFI
variables, and Apple's persistent boot selection were not changed. An actual
Gentoo boot still needs verification by rebooting.

For rollback, mount **Gentoo's** ESP (UUID `48F3-1101`) writable, restore the
backup to its root-level `ubootefi.var`, and remove only the newly copied
`EFI/BOOT/BOOTAA64.EFI`. Do not use Fedora's `/boot/efi` mount for this repair.
Flush writes and unmount cleanly. When updating Gentoo GRUB, keep its fallback
EFI copy updated too.

Background: [Asahi boot process](https://asahilinux.org/docs/alt/boot-process-guide/)
and [platform quirks](https://asahilinux.org/docs/platform/quirks/).

## `reboot-gentoo`

The Zsh function lives in `~/.zsh_functions` (symlinked to this repository).
Load it in an existing terminal with:

```zsh
source ~/.zsh_functions
reboot-gentoo --dry-run
# When ready to end the session:
reboot-gentoo
```

The helper sets Apple's **one-shot** boot target using
`sudo asahi-bless --next --set-boot Gentoo --yes`, verifies that
`--next --get-boot` reports exactly `Gentoo`, then runs `sudo systemctl reboot`.
It does not change the permanent default. Help and dry-run make no changes.
If selection or verification fails, it does not reboot. If reboot itself
fails, the one-shot target remains set; cancel with
`sudo asahi-bless --clear-next` if desired.

Tests use isolated mock executables and never reboot or change boot state:

```sh
zsh -n .zsh_functions
python3 -m unittest discover -s tests -p 'test_reboot_gentoo.py' -v
python3 -m unittest discover -s tests -p 'test_which_one.py' -v
```
