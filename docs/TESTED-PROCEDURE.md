# What was actually done

This is a sanitised record of the successful September 2026 experiment. It describes the original staged commands, not a claim that the newly consolidated wizard has already completed a fresh-device run.

## 1. Establish the limits of normal ADB

The X2i was reachable by network ADB and later USB. Android was a production `user/release-keys` build: ordinary shell UID 2000, `ro.debuggable=0`, and `adb root` refused. No `su` was available in the standard locations.

ShellyElevate and Fully installed as normal apps. WRITE_SETTINGS/Doze permissions were possible, but disabling `cloud.shelly.stargate` failed with `Cannot disable a protected package`. Selecting another HOME activity did not permanently displace the stock app while it retained ownership.

The ShellyElevate privileged-app installer was inspected. It **assumes** `adb root` and a writable system; it does not itself obtain root on a production X2i. USB alone did not make `adb root` work.

## 2. Reach the real bootloader

After USB identity checks, `adb reboot bootloader` exposed a fastboot interface. On Windows it initially lacked a driver (problem code 28). Binding the signed Google Android Bootloader Interface made individual fastboot queries work.

Observed values included `product: evb_px30`, U-Boot 2017.09, `secure: yes`, `unlocked: no`, non-slotted boot, and boot size `0x2800000`. Fetch/readback was unavailable. Some unlock variants were unimplemented. `flashing unlock` returned OKAY but the `unlocked` variable still said no.

Android's `ro.boot.flash.locked=0` / `verifiedbootstate=orange` had looked promising, but the downloadable vendor boot command line hard-codes orange. **Those properties were not proof of a fully unlocked bootloader.**

`getvar all` stalled communication. It is deliberately excluded from the toolkit.

## 3. Locate a vendor image and patch it on the target

The stock APK contained a URL for `JennaUpdateSDIO.zip` on `repo.shelly.cloud`. Although the URL path names an XL model identifier, its archive metadata and the stock updater's device check identify **Jenna**. This is a recorded vendor packaging oddity, not permission to use arbitrary XL images.

The archive contained boot, dtbo, uboot and trust, not the current complete firmware. Its Jenna build was `vJenna.d713ea0` and kernel #82 from November 2025, older than installed `vJenna.0a276d5` / May 2026 kernel #212.

The original device's protected boot partition could not be read before root. With the owner's explicit acceptance of the resulting recovery risk, the downloaded vendor `boot.img` was patched **on that same target** using official Magisk 30.7 components:

```sh
BOOTMODE=true KEEPVERITY=true KEEPFORCEENCRYPT=true PATCHVBMETAFLAG=false sh ./boot_patch.sh vendor-boot.img
```

The temporary image had Android boot header v2 and fit within the 40 MiB boot partition. The exact original boot had not been recovered, so the patched image was an experimental substitute, not a patch of the installed May kernel.

RAM-boot commands returned OKAY, but execution of the intended image was not established; Android later returned with the original kernel and no root. The documentation does **not** count those command responses as a successful RAM-boot root test.

## 4. Boot-only flash and real root proof

After serial/partition checks and the observed unlock command, **only `boot`** was flashed. No full OTA was applied. No `uboot`, `trust`, `vbmeta`, `dtbo`, `super`, recovery or userdata flash/erase was issued.

USB/boot continuation stalled again after reboot/continue. Once the completed write was confirmed, a user-performed cold power cycle brought Android back with kernel #82 and Magisk running.

The decisive verification was:

```sh
/debug_ramdisk/su -c id
# uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

`/debug_ramdisk/magisk -v` reported 30.7. Ordinary adbd remained unprivileged. The root path was `/debug_ramdisk/su`; assuming `/system/bin/su` existed would have been wrong.

Working rooted boot and other boot-related partitions were backed up **after** root. Those snapshots do not recover the original overwritten May boot.

## 5. Finish Magisk and replace the kiosk environment

The running root daemon worked, but `/data/adb/magisk` lacked the manager's usual payload. The same verified APK supplied those userspace files; Magisk's own environment check then passed. No additional boot flash was needed.

An original local Magisk module overlaid the signed existing Elevate APK under `/system/priv-app/ShellyElevateV2/`. Android reported SYSTEM/UPDATED_SYSTEM_APP/PRIVILEGED. The user's existing data and MQTT settings remained intact. System-app status is not platform signing and does not confer every signature-only permission.

The important owner discovery was in `/system/etc/init/stargate.rc`:

```text
on post-fs-data
    copy /system/etc/stargate/device_owner_2.xml /data/system/device_owner_2.xml
    copy /system/etc/stargate/device_admins.xml /data/system/device_admins.xml
```

Removing a data file once would not be persistent. The module therefore overlaid the factory templates with empty records and cleared the Shelly assignment during post-fs-data. The hardware init rules were left intact.

With explicit owner approval, the known stock updater script was overlaid with a no-update guard and Android's automatic-update setting disabled. The price is foregoing security updates through that path until deliberately reviewed/re-enabled.

After a reboot proved the owner absent, both stock APKs were disabled for user 0. Fully's actual `launchOnBoot` preference was enabled and Ultra Small Launcher selected as HOME.

The factory image had left Android's ordinary setup-completion flags at zero. With the stock owner removed, Fully offered managed enrollment. Running Android's built-in `com.android.provision/.DefaultActivity` completed ordinary setup, set both flags to one, and **did not assign a new owner**.

## 6. Persistence and application checks

A second reboot verified root, the privileged module, absent factory ownership, disabled stock apps, the chosen HOME launcher, and Fully launching from its boot intent. The authenticated Home Assistant dashboard rendered correctly. Elevate's background service and existing MQTT reporting were active. Wi-Fi reached the local HA server; an ICMP ping failure alone had not indicated an HTTP connectivity failure.

The complete root result had therefore survived a cold power cycle and two subsequent reboots. This is not a promise of surviving updates, factory reset or module removal.

## Known limitations

- Vendor `android.hardware.memtrack@1.0-service` logged `FORTIFY: readdir: null DIR*` in each captured boot crash log, with a backtrace through `memtrack.rk3326.so`. Dashboard/network/apps remained operational. Whether this is caused by the mixed kernel/vendor versions was not established.
- Elevate temperature/humidity entities remained unknown. Physical brightness control was not proven by a reported MQTT/API value. Stable Elevate had previously encountered direct-sysfs brightness permission issues.
- Relays, audio, long-term stability and a new doorbell-video integration were not validated by this setup work.
- No working exact-current-kernel rooting route, full original firmware restore image or guaranteed maskrom unbrick procedure was established.
- The consolidated script has stricter identity guards, resumable state and privacy handling than the original ad-hoc scripts. Its write stages need validation on another factory-stock device before being described as reproduced end-to-end.

## Primary references

- [Shelly device generation/model table and changelog](https://github.com/ShellyGroup/Wall-Display-Changelog)
- [ShellyElevate installation](https://github.com/RapierXbox/ShellyElevate/wiki/Installation)
- [Magisk installation](https://topjohnwu.github.io/Magisk/install.html)
- [Magisk modules and boot scripts](https://topjohnwu.github.io/Magisk/guides.html)
- [Android 11 owner-state implementation](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-11.0.0_r1/services/devicepolicy/java/com/android/server/devicepolicy/Owners.java)

Upstream generic instructions supply context; the device observations above establish what actually worked here.
