#!/system/bin/sh
# Executed before Android's framework starts. SERIAL is generated per device.
MODDIR=${0%/*}
[ "$(getprop ro.serialno)" = "@SERIAL@" ] || exit 0
[ "$(getprop ro.product.device)" = "Jenna" ] || exit 0
for item in device_owner_2.xml device_admins.xml; do
    target="/data/system/$item"
    [ -f "$target" ] || continue
    if grep -q 'cloud.shelly.stargate' "$target"; then
        cp "$MODDIR/system/etc/stargate/$item" "$target"
        chown 1000:1000 "$target"
        chmod 600 "$target"
        restorecon "$target"
    fi
done
date > /data/adb/shelly-owner-override.log
