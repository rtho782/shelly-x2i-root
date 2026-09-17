# SystemUI method patches

These smali files document the exact code changes tested with the original SystemUI SHA256 `a9e2a829ad3f6b17176a16376a2dd9c5039c670daf40c7c7347298f79b121755`. Read [the full manual procedure](../NATIVE-NAVIGATION.md) first.

They are inert source assets: no setup script loads them. No stock vendor APK, complete decompiled vendor class or patched vendor APK is distributed.

## Files and origin

- `patches/NavigationBarFragment.create.smali`: replacement for the one static method, adapted from [AOSP Android 11 NavigationBarFragment.create](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-11.0.0_r1/packages/SystemUI/src/com/android/systemui/statusbar/phone/NavigationBarFragment.java). Copyright (C) 2017 The Android Open Source Project.
- `patches/RestoredNavigationAttach.smali`: complete new helper class, adapted from that method's anonymous attach-state listener. Copyright (C) 2017 The Android Open Source Project.
- `patches/StatusBarWindowController.attach.smali`: replacement for the one method, adapted from [AOSP android11-release StatusBarWindowController.attach](https://github.com/aosp-mirror/platform_frameworks_base/blob/android11-release/packages/SystemUI/src/com/android/systemui/statusbar/phone/StatusBarWindowController.java). Copyright (C) 2019 The Android Open Source Project.

Modified in 2026 for this experiment: Java implementations expressed as smali; the attach listener separated into a named helper; retained vendor resources addressed using verified numeric IDs; package name supplied directly because the vendor build stripped the original context field; navigation title fixed to the tested default display (`NavigationBar0`). This is not a general multi-display patch.

All three adaptations are distributed under **Apache License 2.0**, not the root MIT licence. A full copy accompanies the [AOSP notice and licence](../../third_party/quickstep/NOTICE.txt). They are provided without warranty. The source links and copyright notices above identify the upstream works; neither AOSP nor Shelly endorses this experiment.

## Exact-build resource mapping

| Resource | Value in the original APK |
|---|---|
| `id/navigation_bar_frame` | `0x7f0a0327` |
| `layout/navigation_bar_window` | `0x7f0d0105` |
| `string/nav_bar` | `0x7f11046b` |

The vendor's resources and manifest remain untouched. Do not infer these identifiers from another firmware or substitute them into a different APK. The two method files must be inserted into their existing classes; treating them as complete class files will not build correctly.
