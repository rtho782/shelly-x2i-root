# Native Android navigation restoration

This is a **separate, experimental manual modification**, successfully tested on the already-rooted X2i described in [the tested procedure](TESTED-PROCEDURE.md). It is **not implemented by `x2i.py`**. The root/setup scripts, existing module and tests have not been changed to perform it.

## Result and limits

On the single tested Shelly X2i / Jenna, firmware **2.7.4-b7b6bc07**, Android 11 / API 30:

- Real Android Back and Home buttons work.
- The square Recents button opens the stock Android 11 task switcher; selecting Fully's preview returns to Fully.
- Swiping up from the bottom in Fully reveals the native bars, which subsequently auto-hide. This was checked on the physical panel and again after reboot.
- Ultra Small Launcher (`l.l/l.l`) remains the default Home app. Restoring Recents does not require replacing it with Quickstep as Home.
- Root and the existing ShellyElevate/owner-removal/update-blocking setup remain intact.
- The native bar retains the vendor layout: volume down, Back, Home, Recents and volume up. Volume-button presence was observed; audio behavior was not separately validated.
- Both new components survived a reboot. Long-term stability, other firmware builds, multi-display operation and Android's gesture-navigation mode are **not** established.

The original system partition was not rewritten. Two independent Magisk modules provide the changed SystemUI APK and the missing Quickstep app. This is not an accessibility-button overlay or a replacement navigation app.

## Why settings alone did not work

The stock SystemUI APK contains the layouts and much of the implementation, but these two methods are stubs:

```text
com.android.systemui.statusbar.phone.NavigationBarFragment
  static create(Context, FragmentHostManager.FragmentListener): View
    returns null

com.android.systemui.statusbar.phone.StatusBarWindowController
  attach(): void
    returns immediately
```

Android already reported `config_showNavigationBar=true`, three-button navigation (`navigation_mode=0`), completed provisioning, no active lock-task mode and no status-bar disable flags. Starting SystemUIService or sending the vendor `com.smatek.show.navigationbar` broadcast did not overcome those stubs. Those diagnostic changes were reverted before patch testing.

The framework also names `com.android.launcher3/com.android.quickstep.RecentsActivity` as its Recents provider, but `com.android.launcher3` was missing. Restoring only the bars therefore gives Back/Home but leaves the square button without a working task switcher.

## Files supplied, and deliberately omitted

| Component | Repository contents | Reason |
|---|---|---|
| Stock Android 11 Quickstep | [APK, original permission XML, notices and provenance](../third_party/quickstep/) | The exact official image's licence notice identifies this APK as Apache-2.0 licensed. |
| SystemUI changes | [Two method replacements and one helper class](native-navigation/patches/) | AOSP-derived smali source, with attribution and Apache-2.0 terms. |
| Shelly SystemUI APK, original or patched | **Not included** | Redistribution permission for the complete vendor-modified binary has not been established. Obtain the original from your own matching panel. |
| Ready-made navigation module ZIPs | **Not included** | The tested SystemUI module embeds that vendor APK; the private trial installers also contained a device-specific guard. They are not general-purpose downloads. |

Do not substitute the SystemUI APK from the Google emulator image: it is not the patched Shelly APK. The emulator image is only the source of Quickstep. No emulator firmware is flashed onto the panel.

## Compatibility and hashes

The original SystemUI path is `/system_ext/priv-app/SystemUI/SystemUI.apk`.

| Artifact | SHA256 |
|---|---|
| Required original Shelly SystemUI APK | `a9e2a829ad3f6b17176a16376a2dd9c5039c670daf40c7c7347298f79b121755` |
| Locally tested patched SystemUI APK, not distributed | `474ef53c25477b4a4f127e2bf69eabcf84c122f414088bb843316670c5b75f8c` |
| Supplied, unmodified Launcher3QuickStep APK | `9b6fd0b6d5188bf2904c2419163fd440a95c6f181eeef9756e376aa8c05228e3` |
| APKTool 3.0.3 used for the DEX rebuild | `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423` |

The marketing firmware version is insufficient: **stop if the original APK hash differs**. The smali uses resource IDs from this exact APK. The patched hash is historical evidence, not a promise that every ZIP repacker produces identical bytes.

Quickstep is the API-30 `com.android.launcher3` package, versionName `11`, versionCode `30`, with no shared UID and no native libraries. Its `TouchInteractionService` is the native interface used by this SystemUI.

## Reproduction outline for experienced Android developers

This is a record of the successful method, not an unattended installer. It assumes working Magisk root, USB ADB, reliable power, a private original-APK backup and a tested way to disable your new modules if Android fails. Read [the safety notes](SAFETY.md). SystemUI mistakes can cause a UI crash loop or prevent usable boot; a watchdog does not guarantee recovery.

### 1. Back up and inspect your own APK

Use your physical USB serial, never another panel's identity. These commands are read-only on the device:

```sh
adb -s YOUR_USB_SERIAL shell sha256sum /system_ext/priv-app/SystemUI/SystemUI.apk
adb -s YOUR_USB_SERIAL pull /system_ext/priv-app/SystemUI/SystemUI.apk SystemUI-original.apk
```

Keep the backup private and confirm the hash above. Also record the current Home selection, Magisk modules and Android build. Do not bypass a mismatch by merely changing a hash constant.

### 2. Restore the missing implementations

Use [official APKTool 3.0.3](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3) and Java. Decode without rebuilding resources:

```sh
java -jar apktool_3.0.3.jar d --no-res -o SystemUI-work SystemUI-original.apk
```

Under `SystemUI-work/smali/com/android/systemui/statusbar/phone/`:

1. Replace **only** the complete `NavigationBarFragment.create(...)` method with [NavigationBarFragment.create.smali](native-navigation/patches/NavigationBarFragment.create.smali).
2. Replace **only** the complete `StatusBarWindowController.attach()` method with [StatusBarWindowController.attach.smali](native-navigation/patches/StatusBarWindowController.attach.smali).
3. Add the complete [RestoredNavigationAttach.smali](native-navigation/patches/RestoredNavigationAttach.smali) class.

The first two files are method snippets, **not replacements for the entire class files**. Confirm the originals are the known stubs before editing. The helper attaches/detaches the NavigationBar fragment using the existing FragmentHostManager. Resource identifiers are explained in the [patch notes](native-navigation/README.md).

Reassemble the code:

```sh
java -jar apktool_3.0.3.jar b SystemUI-work -o rebuilt-code.apk
```

**`rebuilt-code.apk` is an intermediate, not an installable final payload.** Do not install it on the device.

### 3. Repack without changing the resources or package identity

The tested private builder performed this deliberately narrow operation:

1. Take `classes.dex` from `rebuilt-code.apk`.
2. Repack the original APK's entries in their original order, replacing only that entry. Preserve the original binary manifest, resources and every other entry's uncompressed contents. Align uncompressed entries to four-byte boundaries.
3. Retain the original APK Signing Block (the block immediately before the ZIP central directory, identified by `APK Sig Block 42`), insert it before the new central directory and update the ZIP end record's central-directory offset.
4. Verify the ZIP, compare all entry names and contents, and require that **only `classes.dex` changed**. Require the retained signing block to match the original byte-for-byte.

**Retaining the signing block does not make the modified APK's cryptographic signature valid.** It is not vendor-signed modified software, cannot be installed with ordinary `adb install` / `pm install`, and must not be re-signed with an arbitrary test key. The successful experiment used a systemless replacement at the original trusted system path, preserving the existing package's certificate identity. No global signature-verification bypass was installed.

This behavior was verified on the exact rooted firmware above; it is not guaranteed on other Android/vendor builds. See Android 11's [system-partition scanning implementation](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-11.0.0_r1/services/core/java/com/android/server/pm/PackageManagerService.java), particularly `collectCertificatesLI` and the system-partition `skipVerify` path. Resource-preserving repacking and signing-block retention are not automatically provided by the APKTool commands above. No repacking/installation automation is added to the toolkit in this documentation update.

### 4. Validate temporarily before making it persistent

The successful experiment staged the candidate in `/data/local/tmp/`, ran Android's `dex2oat64` with `--compiler-filter=verify`, then temporarily bind-mounted it over the original APK in Magisk's **global mount namespace** (`su -mm`). It restarted only `com.android.systemui`, not zygote or system_server.

A separately running, three-minute rollback helper was armed **before** the mount. It checked the candidate's hash, unmounted only the exact SystemUI APK path, checked the restored original hash and restarted SystemUI unless explicitly cancelled after validation. A reboot also removed this temporary mount. Only after stable native Back/Home behavior was demonstrated was persistence attempted.

Do not skip this staged test or assume a successful DEX verifier proves runtime compatibility. Do not remove ART caches indiscriminately. The original vendor `oat` files did not need deleting in the successful test.

### 5. Add separate Magisk modules and reboot-test

The tested module layouts were:

```text
shelly_native_navigation/
  module.prop
  service.sh                         # bounded boot guard, described below
  system/system_ext/priv-app/SystemUI/SystemUI.apk

shelly_stock_quickstep/
  module.prop
  system/system_ext/priv-app/Launcher3QuickStep/Launcher3QuickStep.apk
  system/system_ext/etc/permissions/com.android.launcher3.xml
```

Use the [included Quickstep APK](../third_party/quickstep/Launcher3QuickStep.apk) and [original permission XML](../third_party/quickstep/com.android.launcher3.xml) unchanged. Magisk's normal installer supplies root ownership, standard system-file contexts and permissions. APK/XML files are mode `0644`, directories `0755`, and the boot script is executable. Follow the official [Magisk module format](https://topjohnwu.github.io/Magisk/guides.html); these folder sketches are **not** complete ready-to-install ZIPs.

The tested `service.sh` was a bounded late-start guard: it allowed approximately three minutes for boot completion, then required the same nonempty SystemUI PID over seven consecutive three-second intervals and a `NavigationBar0` window. If those checks failed, it marked **only these two new modules** disabled and requested a reboot. On success it logged a healthy boot and exited. It was not a continuous application watchdog. Its successful path was observed; the failure/recovery path was not deliberately induced or proven to recover every failure.

The permission XML grants the original app-specific allowlist. Do not globally relax privileged-permission enforcement. There was no need to change the default Home app to Quickstep or to enable Shelly's stock launcher. The existing `shelly_elevate_system` module stays separate.

### 6. Verify the result

Check on-screen Back/Home from Android Settings, Recents, selecting an existing task, bottom-edge reveal and auto-hide in Fully. Then verify again after reboot:

```sh
adb -s YOUR_USB_SERIAL shell getprop sys.boot_completed
adb -s YOUR_USB_SERIAL shell pidof com.android.systemui
adb -s YOUR_USB_SERIAL shell pm path com.android.launcher3
adb -s YOUR_USB_SERIAL shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME
adb -s YOUR_USB_SERIAL shell dumpsys activity services com.android.launcher3
adb -s YOUR_USB_SERIAL shell logcat -d -s AndroidRuntime:E
```

Quickstep's service should be bound by `com.android.systemui`; the Home selection should remain the previously chosen launcher. Verify actual root with your installed Magisk `su -c id`. Absence of a standalone `SystemUIService` record is not itself a failure on this firmware: SystemUI's application, windows and Quickstep binding were operational without that service record.

No screenshots, raw logs, serial numbers, household URLs or configuration exports from the test panel are published here.

## Rollback

In Magisk, disable the two new navigation/Quickstep modules and reboot. Keep the existing Elevate/owner/OTA module enabled.

If the Android UI is unusable but USB ADB and root still work, run the following **inside an authenticated root shell on your selected panel**, for the exact module IDs above:

```sh
touch /data/adb/modules/shelly_native_navigation/disable
touch /data/adb/modules/shelly_stock_quickstep/disable
reboot
```

That removes the new systemless mounts on the next boot; it does not erase app data, remove Magisk, reset the panel or re-enable Shelly software. After persistent installation, **reboot alone does not undo the patch**. If ADB/root are unavailable, this command path cannot help: have a recovery plan before modifying SystemUI.

## Licence and provenance

Quickstep's included [licence/provenance record](../third_party/quickstep/README.md) documents the exact image notice and the SDK open-source exception. The supplied patch snippets are adaptations of AOSP methods under Apache-2.0, with notices in [the patch directory](native-navigation/README.md). The repository's MIT licence does not relicense these third-party components. Permission to redistribute the complete Shelly-modified SystemUI binary remains unverified, so it is excluded.
