# Validation status

## Established on the original panel

The original, individually executed procedure achieved persistent root, systemless Elevate promotion, owner override, stock-app disable and Fully automatic dashboard startup. See [the device experiment](TESTED-PROCEDURE.md). This is one device, not a hardware compatibility certification.

## Consolidated toolkit

On 17 September 2026:

- The standard-library unit suite passed locally on Windows/Python 3.12.
- `x2i.py inspect` and `x2i.py verify` were run successfully against the already-rooted original X2i using its USB serial. These checks did not flash, reinstall, reboot or alter its application configuration.
- Source compilation and command-line help checks passed.
- Safety tests cover compatibility rejection, USB-only serials, URL credential rejection, pinned-file corruption, boot header/size validation, owner-template validation, XML preference preservation, explicit missing-backup acknowledgement, serial-specific confirmations, no reflash after an attempted write, stopping on an ambiguous flash response, and resuming staged setup without another flash.
- GitHub Actions runs the hardware-free tests on Windows and Linux with Python 3.10, 3.12 and 3.13. A green workflow validates the wrapper tests, not fresh-device hardware behavior.
- Display-mode tests cover explicit Lite/Full selection, no default dashboard URL, propagation of the caller's URL, Fully installation only for Lite, selected foreground-app checks, and saved-mode/legacy-state resumption. Full mode's existing-Fully handling only disables its boot launch, preserving the URL and other data.
- Both modes set and verify Ultra Small Launcher as default Home, independently of the stock-owner override option. Mock tests reject a missing launcher or a wrong Home selection even without that override. A read-only check and ordinary Home launch on the original panel confirmed the launcher was already installed/default and could open.

**Not yet validated:** the entire consolidated `wizard` sequence on a second factory-stock 2.7.4 device, or the Full Elevate display recipe on hardware. In particular, freshly creating app preferences, USB-driver pauses and the combined resume paths remain operational assumptions derived from the original manual work. The original panel uses Lite + Fully; source inspection of Elevate's boot receiver/watchdog supports the Full mode design but is not a hardware startup test. The code is intentionally labelled experimental 0.1.

Do not repeat a boot flash on an already-working panel just to turn this limitation into a success claim. A meaningful next test is another owned, matching unit with explicit risk acceptance and a recorded fresh-device run.
