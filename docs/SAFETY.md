# Safety and recovery limits

## Before starting

This experiment was undertaken on an owner's personal X2i with explicit acceptance of bricking risk. It is not a supported manufacturer procedure. The safe outcome for a mismatched device is to stop, not to remove the script's safeguards.

- The exact original boot partition was inaccessible from the production ADB shell and was **not backed up before replacement**. Bootloader fetch was unsupported. The downloadable older image is not a full restore image for the tested current build.
- The bootloader returned success to `flashing unlock`, but continued reporting `unlocked: no`. The successful boot write is an observation; a general bootloader unlock is **not established**. Other units may reject it or erase userdata.
- The replacement boot brings an older kernel. It retains existing Android/vendor partitions rather than downgrading the entire firmware. Compatibility and long-term reliability are not established.
- A single successful unit does not establish fleet-wide compatibility. Hardware revisions may exist under the same product name or advertised firmware version.
- This is mains-powered equipment. Use the manufacturer's safe USB/power arrangement, isolate mains before handling wiring, and involve a qualified person where required. Never disconnect power during an active partition write.

Do not use the toolkit on workplace-managed devices, somebody else's equipment, unknown hardware, legacy X2/Pegasus, XL/Blake, X1i/Cally or an NSPanel. It is specifically guarded for Jenna.

## What changes

Preparation installs the official Magisk manager and patches a downloaded vendor boot image on the target, in temporary files. Flashing writes the non-slotted `boot` partition only. The optional kiosk step installs apps and grants their declared runtime permissions, then uses a Magisk module to overlay system paths. It does not remount or edit the underlying system partition.

The optional owner override removes Shelly's factory assignment. It does **not** make a human an Android DevicePolicyManager component, assign ownership to Fully, or enroll the device into another management service. Ordinary personal control is the goal. Finishing Android's built-in provisioning sets `device_provisioned` and `user_setup_complete` to 1.

The stock launcher/placeholder remain installed but disabled. Android and vendor hardware services still run: disabling the Shelly applications is not equivalent to removing all vendor firmware.

The updater guard deliberately prevents the identified stock firmware update path. This includes security fixes. It is reversible and is neither a network firewall nor a defence against deliberate bootloader/recovery flashing.

## Existing security posture

The tested stock unit reported SELinux **Permissive**, `ro.adb.secure=0`, and an old Android security-patch date. These were observations before rooting, not security settings this toolkit weakened. Do not infer that a later Shelly app version updates the Android kernel or security patch.

Keep ADB and ShellyElevate management interfaces on a trusted, restricted network. Do not expose them to the Internet. Treat a rooted, old-Android panel as a dedicated appliance, not a place to store valuable credentials. The toolkit does not configure your firewall or claim to harden unauthenticated network ADB.

The pinned Elevate HTTP interface is unauthenticated, returns stored settings without secret redaction, and supports WebView JavaScript injection. The kiosk recipe enables this server. Our chosen deployment policy is IoT client isolation plus router restrictions permitting management only from Home Assistant and one administration PC; see [network containment](NETWORK-ISOLATION.md) for scope, limitations and verification. This is not a substitute for firmware security fixes, and other owners should make their own firmware/update and exposure decisions.

The owner reports that wireless ADB needed manual enabling in Android Settings after the stock Shelly app was disabled. Neither `ro.adb.secure=0` nor successful USB/root access establishes that a TCP listener is enabled. The toolkit does not automatically enable wireless ADB.

## What the backups contain

`.local/` may contain your serial, dashboard address, app preferences, ownership records, logs, APKs and boot images. Preferences can include secrets. Keep it private; `.gitignore` is a guardrail, not encryption. Do not paste entire logs into public issues.

Preparation's `vendor-boot.img` is the downloaded older vendor image, **not the original device boot**. A later capture of working rooted boot is also **not** a pre-change backup. The toolkit does not claim a complete firmware/userdata backup. Preserve any exact original images you obtain separately.

## If a command hangs or fails

1. Stop. Read the private stage log and look at the panel.
2. Identify whether Android ADB, bootloader fastboot or neither is present. Query a specific serial only.
3. Avoid `fastboot getvar all`: it stalled the tested bootloader/USB connection. Use individual variables instead.
4. Do not loop flashing. An ambiguous timeout can mean a write occurred; the script records `flash_attempted` before writing for this reason.
5. A complete power cycle recovered stalled USB/boot continuation on the tested unit, **after the write had finished**. It is not a guaranteed unbrick procedure.

The wizard cannot install Windows drivers, reconnect cables, approve Magisk dialogs or guarantee recovery. There is deliberately no automatic Rockchip loader/maskrom flashing routine here.

## Reversing only the optional module

These are manual recovery notes, not an automatic uninstall promise. Read the paths carefully and use your own serial. The toolkit-created module is named `shelly_x2i_toolkit`.

From authorized ADB while Android and root still work:

```sh
adb -s YOUR_USB_SERIAL shell /debug_ramdisk/su -c 'touch /data/adb/modules/shelly_x2i_toolkit/disable'
adb -s YOUR_USB_SERIAL reboot
```

This stops loading the module on the next boot. The original vendor owner templates and updater become visible again; **factory Shelly ownership may return**. Systemless Elevate promotion also disappears. Root in the patched boot image is unaffected by disabling this module.

If you deliberately want stock software active again, re-enable its packages and choose its HOME activity:

```sh
adb -s YOUR_USB_SERIAL shell /debug_ramdisk/su -c 'pm enable --user 0 cloud.shelly.stargate'
adb -s YOUR_USB_SERIAL shell /debug_ramdisk/su -c 'pm enable --user 0 cloud.shelly.placeholder'
```

Restore `ota_disable_automatic_update` to its recorded old value; if it was `null`, delete that setting instead of writing the text `null`. Restoring dashboard/app preferences is a separate step. Be careful with shell quoting on Windows; the toolkit's `root()` helper avoids nested PowerShell quoting issues.

**Returning to the exact original kernel requires the correct original boot image.** Disabling Magisk or its module does not restore that missing image. Do not flash a random “stock” image from another owner. A factory reset also does not reconstruct the original boot partition.
