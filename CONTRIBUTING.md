# Contributions and validation

Keep the support claim narrow. The current evidence is one successful manual device procedure; the refactored wizard has not yet completed a fresh-device reproduction.

For a reproduction report, include non-identifying model, Shelly version/build suffix, Android fingerprint, original and resulting kernel versions, OS/tool versions, stage outcomes, and observed regressions. State whether root was verified by UID 0 after reboot, not just by an orange boot property or an OKAY flash response. Describe whether a true original boot backup existed.

Do **not** upload raw `.local/` contents, serials, IP/MAC addresses, app preferences, screenshots, authentication tokens, MQTT credentials or firmware dumps. Review log snippets manually before posting. A firmware fingerprint is a build identifier; a device serial is private device identity.

Changes to supported fingerprints, artifact pins, firmware-writing commands or recovery instructions require explicit rationale and hardware evidence. Never add broad `getvar all`, erase commands, automatic reflashing on timeout, generic hardware overrides or an unattended confirmation bypass.

Run:

```sh
python -m unittest discover -s tests -v
python -m py_compile x2i.py
```

All tests must work without connected hardware or network access. New device-write stages should have mock-command tests establishing the exact targets and failure behavior. Read-only hardware checks do not replace end-to-end validation of a write workflow.
