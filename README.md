# Shelly X2i root and local-control toolkit

Experimental, community-documented rooting and kiosk setup for the **Shelly Wall Display X2i / Jenna**, tested on **Shelly firmware 2.7.4-b7b6bc07** and the Android build below.

**This is not a general-purpose Shelly unlocker or a proven one-click root.** The underlying procedure worked on one device. The consolidated Python wizard is a refactoring of that procedure, with automated tests and read-only checks on the rooted device; it has **not yet been run end-to-end on a second factory-stock unit**. Use only on a device you own and can afford to lose.

> The successful experiment replaced the boot image with a Magisk-patched **older vendor Jenna boot image**. The original boot could not be backed up first. The result uses a November 2025 kernel with the existing May 2026 Android build. A vendor memory-tracking service crashes at startup. There is no guaranteed recovery route. Read [SAFETY.md](docs/SAFETY.md) before executing write commands.

## What worked

- Magisk 30.7 root, verified by actual `uid=0(root)` execution after a cold power cycle and two further reboots.
- ShellyElevate running as a privileged system app through a reversible Magisk module; no writable-system remount required.
- Preventing the factory firmware from assigning the stock Shelly app as Android device owner on every boot.
- Disabling the stock launcher and placeholder app **without uninstalling their APKs or clearing their data**.
- Ultra Small Launcher as HOME, Fully Kiosk 1.57.1 opening the dashboard automatically, and ShellyElevate starting in the background.
- An explicitly optional block on the identified stock firmware updater, including security updates.
- Separately tested native Back/Home/Recents restoration with fullscreen reveal/auto-hide. See [the navigation-bar fix below](#native-android-navigation-bar-fix); it is **not a feature of the setup script**.

This is **not** a claim that every X2i sensor, relay, audio feature, or hardware service works. See [known limitations](docs/TESTED-PROCEDURE.md#known-limitations).

## Exact tested combination

| Item | Observed value |
|---|---|
| Model / product | SAWD-5A1XX10EU0 / Jenna (X2i, not legacy X2) |
| Chip / architecture | Rockchip rk3326 / arm64-v8a |
| Shelly app firmware | 2.7.4-b7b6bc07; firmware ID 20260803-150127/2.7.4-b7b6bc07 |
| Android | 11 / API 30 |
| Fingerprint | `Shelly/Jenna/Jenna:11/RD2A.211001.002/vJenna.0a276d5:user/release-keys` |
| Reported Android security patch | 2021-10-01 |
| Original kernel | 4.19.232, build #212, May 2026 |
| Replacement kernel | 4.19.232, build #82, 17 November 2025 |
| Boot partition | 40 MiB, non-slotted `boot` |
| Bootloader USB | VID 18D1 / PID D00D, fastboot |
| Android USB | VID 2207 / PID 0006, ADB |

**The marketing firmware number alone is insufficient.** The script refuses other fingerprints, package build suffixes, architectures, and boot layouts. A future device sold with “2.7.4” may differ. Do not remove the checks to force it through.

## Native Android navigation-bar fix

The rooted test panel now has working **native Back, Home and Recents**, including swipe-up-to-reveal and automatic hiding in Fully. This restores Android's own SystemUI navigation/status bars and stock task switcher; it is not a floating-button app or accessibility overlay.

**This is an optional, separately tested manual modification. `x2i.py` does not apply it.** Installing the launcher or completing the root/kiosk wizard does not, by itself, restore the navigation bar. The findings, patch source and required stock Quickstep APK are provided here, but there is no ready-made universal installer.

### Why a launcher or navigation setting was not enough

The Home launcher, navigation bar and Recents screen are different components. Ultra Small Launcher was already installed and selected correctly: an ADB Home key event opened it. What was missing was the on-screen way to reach it.

Inspection of the tested Shelly SystemUI APK found that two methods had been reduced to stubs:

```text
NavigationBarFragment.create(...)       -> returns null
StatusBarWindowController.attach()      -> returns immediately
```

Most of the surrounding Android code, buttons and layouts were still present, but these methods no longer created/attached the bars. Android already reported that navigation was enabled, with three-button mode selected and no active kiosk lock-task or status-bar restriction. Starting SystemUIService or using the vendor's show-navigation-bar broadcast could not repair the missing implementations.

There was a second omission: the firmware pointed Recents at `com.android.launcher3/com.android.quickstep.RecentsActivity`, but the `com.android.launcher3` package was absent. Restoring the bar alone made Back/Home work while the square Recents button still lacked its task switcher.

### What the restoration changes

Two independent, removable Magisk modules address those omissions:

1. **`shelly_native_navigation` — restore the native bars.** Two small AOSP-derived method replacements and an attach-listener helper restore the missing SystemUI implementation. The locally built APK changes only `classes.dex`; its original manifest, resources and other entry contents are preserved. Magisk presents it at the original `/system_ext/priv-app/SystemUI/SystemUI.apk` path without rewriting the system partition.
2. **`shelly_stock_quickstep` — restore Recents.** The unmodified stock Android 11 Quickstep APK, extracted from Google's official default ARM64 image, supplies the missing task-switcher service. It is installed as a privileged system app through Magisk with the image's original app-specific permission XML.

**Ultra Small Launcher remains the default Home app.** Quickstep supplies Recents in the background; it does not have to replace the chosen launcher. The existing Elevate/owner-removal/update-blocking module remains separate, and neither dashboard configuration nor Fully's preferences needed changing.

### What has actually been tested

On the original rooted X2i, including after a reboot:

- Tapping native Back and Home from Android Settings works.
- Tapping the square Recents button opens Android's task switcher; selecting Fully's preview returns to Fully.
- Swiping up from the bottom in fullscreen Fully reveals the native bars, which subsequently auto-hide. This was checked on the physical panel as well as in post-reboot captures.
- Root remains available and Ultra Small Launcher remains the default Home app. SystemUI stayed stable during the checks, with no fatal exception in the inspected AndroidRuntime log.

The restored bar retains the vendor layout: **volume down, Back, Home, Recents, volume up**. The volume buttons were visible; audio behavior was not separately tested. This is button navigation with edge-swipe reveal, **not a claim that Android's full gesture-navigation mode has been validated**. Other firmware versions, multiple displays and long-term stability remain untested.

### Included files and manual workflow

- [SystemUI patch source and resource notes](docs/native-navigation/) — the two replacement methods and helper class, under Apache-2.0.
- [Stock Quickstep APK](third_party/quickstep/Launcher3QuickStep.apk) and [permission XML](third_party/quickstep/com.android.launcher3.xml) — the unchanged components used in the successful test.
- [Quickstep provenance, checksums and licence notices](third_party/quickstep/) — including the exact official image's licence evidence.
- [Detailed manual procedure](docs/NATIVE-NAVIGATION.md) — build/repack requirements, temporary testing, module layout, validation and rollback.

The procedure starts by backing up your own original SystemUI APK and confirming its exact SHA256:

```text
a9e2a829ad3f6b17176a16376a2dd9c5039c670daf40c7c7347298f79b121755
```

**Stop if it differs.** The patch's resource identifiers are specific to that APK; matching “2.7.4” on the screen is not enough. The original or patched Shelly SystemUI binary is not included because redistribution permission for the complete vendor-modified APK has not been established.

At a high level, the successful sequence was: back up and hash-check the original; decode with APKTool without rebuilding resources; apply the three source assets; rebuild and repack only the changed DEX; verify and test a temporary SystemUI replacement with an armed timed rollback; then install the two separate Magisk modules and verify the behavior again after reboot. The [full guide](docs/NATIVE-NAVIGATION.md#reproduction-outline-for-experienced-android-developers) explains the necessary details. Downloading Quickstep alone does not repair Shelly's SystemUI.

### Signing, safety and rollback

The patched SystemUI retains the original APK signing block for the existing system package's certificate identity, but **its modified contents do not have a valid vendor signature**. It is not an ordinary APK update: do not use `adb install` / `pm install` or re-sign it with an arbitrary key. The tested approach relies on the exact rooted firmware's handling of a systemless replacement at the trusted system path; no global signature-verification bypass was installed. APKTool's intermediate output is not, on its own, the final payload.

The first test was a temporary bind mount with a three-minute automatic rollback. After it worked, the persistent module added a bounded boot guard that checks for a stable SystemUI process and native navigation window; if those checks fail, it is designed to disable the two new modules and reboot. **Only the guard's successful path was observed; automatic recovery is not guaranteed.** Modifying SystemUI can still cause a UI crash loop or prevent usable boot. Keep USB ADB, an original backup and a recovery plan available.

To undo the persistent restoration, disable **`shelly_native_navigation`** and **`shelly_stock_quickstep`** in Magisk and reboot. Leave **`shelly_elevate_system`** enabled to retain the existing Elevate/owner/OTA setup. Rebooting alone does not undo an enabled module. If the UI is unavailable but ADB/root still work, the [root-shell rollback commands](docs/NATIVE-NAVIGATION.md#rollback) provide the equivalent path without clearing app data or removing root.

## Requirements

- Python **3.10 or newer**; no pip packages required.
- Official Android [Platform Tools](https://developer.android.com/tools/releases/platform-tools), providing ADB and fastboot.
- A physical USB data connection and reliable power. This panel has **no battery**; unplugging its USB power turns it off. Follow the manufacturer's electrical safety instructions; do not work on exposed mains connections.
- Developer mode and USB debugging enabled. Use [ShellyElevate's installation guide](https://github.com/RapierXbox/ShellyElevate/wiki/Installation) for the device-side steps.
- On Windows, a working **Android Bootloader Interface** driver as well as the Android ADB driver. See [Windows USB notes](docs/WINDOWS-USB.md).
- For the optional **Lite + Fully** kiosk recipe: an official Fully Kiosk **1.57.1** APK downloaded separately from [Fully Kiosk](https://www.fully-kiosk.com/). Only the exact tested APK hash is accepted. No Fully APK or licence is supplied here. The **Full Elevate** recipe does not require Fully.

The local ADB server must already be running. Start it with your chosen Platform Tools installation:

```powershell
adb start-server
adb devices -l
```

Close other software that repeatedly restarts ADB. The toolkit uses the existing localhost server's wire protocol to avoid version-40/version-41 client restart conflicts; it does not kill/restart the server itself.

## Start with inspection — no device changes

Clone/download this repository and run from its directory:

```powershell
python x2i.py inspect --serial YOUR_USB_SERIAL
```

Use the physical serial reported by `adb devices`, **not** `host:5555`. Output and private logs identify the exact device/build. The default command is also `inspect`.

## One-script guided workflow

Read the risk statement first. Choose a display mode explicitly; neither mode is assumed:

- `--elevate-mode lite`: Elevate's background services plus **Fully Kiosk** for the dashboard. Requires `--fully-apk`.
- `--elevate-mode full`: **ShellyElevate's own WebView** displays the dashboard. Fully is not installed; omit `--fully-apk`.

Both modes install **Ultra Small Launcher** and set it as the default Android Home app. The selected dashboard app opens over it; Home and the foreground dashboard are different things. The toolkit verifies the default Home selection immediately and after reboot. Retained stock device-owner policies may prevent or undo launcher selection; the tool stops instead of reporting success. `--remove-stock` remains an explicit opt-in.

Installing a launcher does not install Android's Back/Home/Recents bar or guarantee a swipe-to-reveal gesture on vendor firmware. The ordinary Home action can be tested with `adb -s YOUR_USB_SERIAL shell input keyevent 3`; fullscreen/navigation behavior is separate from the default Home selection.

For the separately tested native restoration, see [the navigation-bar explanation above](#native-android-navigation-bar-fix) and the [detailed manual procedure](docs/NATIVE-NAVIGATION.md). It does not change this wizard or supply a patched Shelly firmware APK.

**There is no default dashboard URL.** You must provide your own `--dashboard` URL. In Lite mode, Fully's `startURL` is exactly that argument; Elevate's `webviewUrl` is set to it in both modes. No household IP, private hostname, dashboard path or authentication is embedded. The `dashboard.example.invalid` address below is a non-working placeholder: replace it before running.

This Lite example opts into root, kiosk setup, removal of factory ownership/stock apps, and blocking stock firmware updates:

```powershell
python x2i.py wizard --serial YOUR_USB_SERIAL --fastboot "C:\platform-tools\fastboot.exe" --allow-no-stock-backup --kiosk --elevate-mode lite --fully-apk "C:\Downloads\Fully-Kiosk-Browser-v1.57.1.apk" --dashboard "https://dashboard.example.invalid/" --remove-stock --block-updates
```

Or use Full Elevate with the same root/policy choices:

```powershell
python x2i.py wizard --serial YOUR_USB_SERIAL --fastboot "C:\platform-tools\fastboot.exe" --allow-no-stock-backup --kiosk --elevate-mode full --dashboard "https://dashboard.example.invalid/" --remove-stock --block-updates
```

Full mode's setup path is covered by mock tests and the app's boot/watchdog behavior was inspected in source; **it has not been hardware-validated**. The original working panel uses Lite + Fully. If Fully is already installed when setting up Full mode, its preferences are backed up and its `launchOnBoot` is disabled to avoid competing displays. Its URL, other preferences and data are preserved; it is not uninstalled.

Both profiles use fixed brightness 180, disable Elevate's screensaver/automatic brightness, voice assistant/wake and Bluetooth proxy, and enable its HTTP server. Review these preferences and network exposure for your own installation. Full mode refers to Elevate's foreground/WebView mode; it does not automatically enable every optional feature.

On Linux/macOS, omit `--fastboot` if it is on PATH and, for Lite mode, use your local Fully APK path. Host-side unit tests run on Windows/Linux; actual hardware testing was on Windows. Other hosts are not hardware-validated.

The wizard asks for typed, serial-specific confirmations before preparation, flashing, and kiosk setup. There is deliberately **no unattended `--yes` mode**.

1. Inspect and enforce the known compatibility fingerprint.
2. Download SHA256-pinned vendor/Magisk artifacts and patch the vendor boot **on the selected target**.
3. Require acknowledgement of possible data loss and the missing original boot backup.
4. Enter fastboot, verify serial/product/boot size/slot layout, issue the observed unlock command, then flash **only `boot`**.
5. Wait for Android. A driver installation or physical power cycle may require a manual pause.
6. Verify actual Magisk root; approve the shell root prompt on the panel if requested.
7. Optionally install the pinned kiosk apps, save selected configuration backups, stage the reversible module, and reboot.
8. Verify owner removal, disable the stock apps, complete ordinary Android provisioning without assigning another owner, select HOME, and reboot again to check persistence and app startup.

It does not flash `uboot`, `trust`, `dtbo`, `vbmeta`, `super`, recovery or userdata. The full vendor update ZIP is **never applied**. The bootloader's unlock operation itself may behave differently on other units, including wiping data.

### Pauses and resuming

All generated files go under ignored `.local/`. State is bound to the selected USB serial. Keep this directory between stages.

- If the bootloader driver is missing, install/bind it, then rerun the same wizard. Preparation is reused.
- If the boot flash was attempted, the tool **will not automatically flash again**, even if the previous response was ambiguous. Inspect its logs and the physical screen.
- After a successful flash but failed startup wait, a complete power cycle may be required. Reconnect and run `verify`, then `setup` with the kiosk options from above.
- If setup has staged its module and rebooted, run `finish --serial YOUR_USB_SERIAL` to continue. The selected mode is saved locally; you do not need to supply the URL or APK again. Older saved setups without a mode field retain their original Lite + Fully meaning. A conflicting mode on resume is rejected: this setup tool is not an in-place mode switcher. If staging failed partway, stop and review the logs/module; do not assume it is complete.
- If the wizard was interrupted after completion, rerunning it checks the existing result rather than reflashing.

Available stages:

```text
inspect  Read-only inventory (also the default).
prepare  Download, install Magisk manager, patch in temporary files; no flash.
flash    Explicitly confirmed, boot-only experimental write.
verify   Read-only root/status verification; never launches apps or flashes.
setup    Optional pinned kiosk setup and systemless policy/module installation.
finish   Resume a fully staged setup; disable stock apps and test another reboot.
wizard   Guided orchestration of those stages, with state-based resumption.
```

Use `python x2i.py --help` for options. `--remove-stock` and `--block-updates` are separate choices and only apply with `--kiosk`.

## Home Assistant and MQTT

The script configures your supplied dashboard URL and your explicit choice of ShellyElevate Lite or Full mode. **It does not copy anyone's HA authentication, create HA users, or provision MQTT credentials.**

After installation, sign into your own Home Assistant in the selected browser (Fully for Lite, Elevate for Full). Configure ShellyElevate's MQTT connection and discovery using [its HA integration documentation](https://github.com/RapierXbox/ShellyElevate/wiki/Home-Assistant-Integration). Use your own local credentials and unique MQTT device ID. Lite Mode leaves the dashboard display to Fully while Elevate supplies its background services.

Your dashboard, MQTT, sensor availability and permissions still need per-device testing. Fully's boot setting is **`launchOnBoot`**, not `autoStart`.

## Root and update persistence

Root is in the boot partition, not a one-time RAM boot. The tested cold/warm reboots retained it. This does **not** promise survival through factory reset, replacing boot, recovery flashing, disabling Magisk or every possible future update mechanism.

With `--block-updates`, Android's automatic-update preference is disabled and the known stock updater entry point is replaced with a reversible no-update guard. That also blocks security updates through this path. It is not a network firewall and does not prevent deliberate manual flashing. Third-party app updates are not globally blocked by this flag.

## Documentation, testing and privacy

- [Tested manual procedure and findings](docs/TESTED-PROCEDURE.md)
- [Safety, limitations and recovery](docs/SAFETY.md)
- [Windows USB/fastboot troubleshooting](docs/WINDOWS-USB.md)
- [Artifact provenance and hashes](docs/ARTIFACTS.md)
- [Native navigation and Recents restoration](docs/NATIVE-NAVIGATION.md)
- [Contribution and validation rules](CONTRIBUTING.md)

```powershell
python -m unittest discover -s tests -v
python -m py_compile x2i.py
```

Tests use synthetic/mock devices; they do not flash or modify hardware. Inspection/verification on an already-rooted unit does not validate the fresh-device wizard. Do not describe the latter as fully tested until a new-device run is recorded.

Never commit `.local/`, backups, device-derived APKs, boot images, screenshots, device serials, MACs, private IPs, dashboard configs, MQTT passwords or HA tokens. The sole binary exception is the explicitly licence-reviewed, unmodified [AOSP Quickstep APK](third_party/quickstep/) extracted from an official public image, with provenance and notices. No household device dump or patched vendor SystemUI is distributed.

## Credits and licence

This work depends on [Magisk](https://github.com/topjohnwu/Magisk), [ShellyElevate](https://github.com/RapierXbox/ShellyElevate), Android Platform Tools, Shelly's published vendor image, Fully Kiosk, and [Ultra Small Launcher](https://blakadder.com/nspanel-pro-sideload/#install-a-launcher). They retain their own licences and ownership. No endorsement by these projects or Shelly is implied.

Original toolkit code and documentation: [MIT](LICENSE). The supplied [Quickstep component](third_party/quickstep/) and [AOSP-derived navigation patch snippets](docs/native-navigation/) retain their Apache-2.0 terms and notices; they are not relicensed under MIT. Other downloaded scripts/binaries remain under their upstream terms. No vendor firmware or modified Shelly APK is mirrored here.
