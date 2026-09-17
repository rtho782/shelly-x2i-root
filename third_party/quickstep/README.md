# Stock Android 11 Quickstep

This directory supplies the **unmodified** APK and original privileged-permission XML used in the Shelly X2i native-navigation experiment. It restores the missing Android Recents provider. It is not a generic replacement SystemUI, a rooting tool, or part of the existing `x2i.py` workflow.

Read [the native-navigation documentation](../../docs/NATIVE-NAVIGATION.md) before using it. Installing it as an ordinary downloaded app is not equivalent to the tested privileged/systemless installation. Do not change the default Home app just to make Recents available.

## Contents

- `Launcher3QuickStep.apk`: `com.android.launcher3`, version 11 / versionCode 30, min/target API 30; 8,383,535 bytes.
- `com.android.launcher3.xml`: original app-specific privileged-permission allowlist from the same image.
- `NOTICE.txt`: the exact notice content associated with this APK in the image, with XML/HTML quote escaping decoded for readability. Includes the full Apache-2.0 licence.
- `provenance.json`: source paths, checksums, version and licence evidence.

APK SHA256: `9b6fd0b6d5188bf2904c2419163fd440a95c6f181eeef9756e376aa8c05228e3`.

## Source and extraction

Official source: [Google's default Android 11 ARM64 emulator image, revision 2](https://dl.google.com/android/repository/sys-img/android/arm64-v8a-30_r02.zip), as listed in the [SDK image catalog](https://dl.google.com/android/repository/sys-img/android/sys-img2-1.xml). This is the default AOSP image, not the Google APIs or Play Store image.

The archive's SHA1 matched the catalog value `e96298145a5e0bfd6da4816f51b06c520d8dba72`. SHA1 is recorded as the publisher's historical checksum, not a modern signature or proof of authenticity by itself. The APK has the independent SHA256 above.

7-Zip 25.01 was used locally to extract:

```text
arm64-v8a-30_r02.zip
  arm64-v8a/system.img                    # GPT image
    1.super.img                          # logical-partition container
      system_ext.img
        priv-app/Launcher3QuickStep/Launcher3QuickStep.apk
        etc/permissions/com.android.launcher3.xml
        etc/NOTICE.xml.gz
```

No image was flashed. Only the APK and permission XML were installed on the test device. The binary is byte-for-byte the extracted official artifact, not a recompiled or re-signed APK and not a dump of a household panel's installed app.

## Redistribution basis

This is a component-specific licence check, not an assumption that every Android firmware APK may be mirrored:

1. The same image's `system_ext/etc/NOTICE.xml.gz` explicitly maps `/system_ext/priv-app/Launcher3QuickStep/Launcher3QuickStep.apk` to content ID `9645f39e9db895a4aa6e02cb57294595`. That content identifies The Android Open Source Project and supplies Apache License 2.0. The original notice archive's SHA256 is recorded in `provenance.json`.
2. [Android SDK terms, section 3.5](https://developer.android.com/studio/terms), leave use and redistribution of open-source components to their applicable open-source licences.
3. [Apache-2.0 sections 2 and 4](https://www.apache.org/licenses/LICENSE-2.0) allow object-code redistribution subject to the licence and notice conditions. Those notices and the full licence are included here. The XML also retains its original AOSP copyright/licence header.

The APK and XML were not modified. AOSP retains its rights; the repository's MIT licence does not relicense them. No trademark permission or endorsement is claimed. This review does **not** establish rights to redistribute Shelly's modified SystemUI APK, the entire SDK image, Fully Kiosk or other firmware components.
