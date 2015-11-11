# check_filesystem #
check filesystem for manipulations


This project assumes that you have already protected your system with a full disk encryption.

Unfortunately, even with a FDE `/boot` (and `/boot/efi` with UEFI systems) have to be unencrypted. This poses a significant security risk.

## Other solution(s) ##

* [chkboot](https://wiki.archlinux.org/index.php/Dm-crypt/Specialties#chkboot)
  This is basically a nice concept, but it suffers four major drawbacks:
  * You cannot execute it from outside
  * It doesn't support LUKS
  * It isn't configurable easily (without meddling in bash scripts, yuck!)
  * It assumes too much about the system, like a full blown lsb-functions or a filled `/var` directory

* t.b.c.

## The concept ##

### JSON nodes ###

This project only has one additional file, which is also the only (but necessary!) parameter for `check.py`. Ths configuration file is constructed as follows:

    {
        "devicename a" : {},
        "devicename b" : {},
        "devicename c" : {},
    }

These devices are nodes within `/dev`, basically your drives, partitions and so on.

    {
        "/dev/sda":
        {
            "size": 524288,
            "sha256": null
        },
        "/dev/sda1":
        {
            "sha256": null
        },
        "/dev/sda2":
        {
            "luksHeader": null
        },
    }

We have now three options: `size`, `sha256` and `luksHeader`:

* `luksHeader` stores the SHA256 value of the dumped LUKS header, which is read via `cryptsetup luksHeaderBackup`
* `sha256` stores the "normal" SHA256 value of an entire disk, partition or file (the *target*)
* `size` is useful if you want to calculate and store the SHA256 value of a part of a target

### `null` vs value ###

If one value of `sha256` or `luksHeader` is `null`, it is assumed to be *unknown* - the script realizes that the values should be read from the system and stored in the JSON document. Every other value is treated as a valid SHA256 sum and compared against the current value.

The central point is that you can use the same file for storing the values at a "known good" point and compare them later in a more hazardous environment, probably running from a removable medium like [grml](https://grml.org).
