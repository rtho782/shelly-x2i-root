#!/system/bin/sh
# Deliberate opt-in: blocks this stock OTA entry point, including security updates.
# Disabling the module restores the original updater on the next boot.
log -p w -t ShellyRootGuard "Stock firmware update blocked to preserve rooted boot; review manually."
exit 1
