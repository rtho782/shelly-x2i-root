# Artifact provenance and pins

No APK, firmware, partition dump, prepatched image or private key is distributed in this repository. The script downloads upstream files into ignored `.local/downloads/` and fails closed on a hash mismatch. Never “fix” a mismatch by replacing the expected hash without investigating the upstream change.

| Artifact | Provenance | SHA256 |
|---|---|---|
| JennaUpdateSDIO.zip | [Shelly vendor server](https://repo.shelly.cloud/firmware/SAWD-3A1XE10EU2/stable/JennaUpdateSDIO.zip); URL found in stock APK | `e5e362894448784934b0ddb270ee0bcce8f9fe0ab3b459230384f1208917dd05` |
| boot.img inside that archive | Jenna vJenna.d713ea0; November 2025 kernel | `5c9635d64717462a9a595ac5527dd9ade6e23864b6f7e2df735636b685635a81` |
| Magisk-v30.7.apk | [Official Magisk v30.7 release](https://github.com/topjohnwu/Magisk/releases/tag/v30.7) | `e0d32d2123532860f97123d927b1bb86c4e08e6fd8a48bfc6b5bee0afae9ebd5` |
| ShellyElevateV2-3.26170.1325.apk | [Upstream release v3.26170.1522](https://github.com/RapierXbox/ShellyElevate/releases/tag/v3.26170.1522); runtime versionName 3.26170.1323 | `9c841ddd1b69df20f8872afe2354b082446cfafcbff77f6f5877a15294522172` |
| ultra-small-launcher.apk | [Blakadder-hosted installer](https://blakadder.com/assets/files/ultra-small-launcher.apk), linked by Elevate instructions | `e5ffe9eab011942556e151cd80e761dd0574d8998ac0ef5717074ddd80abb8d3` |
| Fully Kiosk Browser 1.57.1 APK | Previously obtained official installer; user supplies their own copy from [Fully Kiosk](https://www.fully-kiosk.com/) | `7867b11e830286eb3f9c4521305603f4225f003e49ea27908eb2e18454125368` |

The differing Elevate tag, filename and runtime version are recorded deliberately, not assumed identical. An experimental newer release was known but was not used in the successful setup.

The original per-device patched candidate's hash was `ebf283ea5008bcda6c483ac0704a608b9cd67ece85212fb9b9236a49ff7088e4`. That is historical evidence, **not an image to download or blindly apply to other panels**. Each run patches on its selected device and records/checks its own resulting hash before flashing.

Magisk's needed components are extracted from its verified APK at runtime. This project does not redistribute its binaries or source under the toolkit's MIT licence. Platform Tools and USB drivers are likewise obtained independently under their upstream terms.
