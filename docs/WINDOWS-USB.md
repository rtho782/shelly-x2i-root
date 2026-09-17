# Windows USB and bootloader notes

The original work used Windows with native Platform Tools. WSL was available but unnecessary. Android ADB and bootloader fastboot are different USB interfaces and may need different driver bindings.

## Android mode

- Tested hardware ID: `USB\VID_2207&PID_0006`.
- `adb devices -l` should show a physical serial in `device` state.
- The script requires that exact serial and verifies `ro.serialno` after connecting.
- It will not accept a Wi-Fi `IP:port` target for a flashing workflow.

## Bootloader mode

- Tested hardware ID: `USB\VID_18D1&PID_D00D`.
- The device appeared as a USB download gadget, initially with Device Manager problem code 28 (driver missing).
- Manually selecting the signed Google **Android Bootloader Interface** driver made `fastboot -s YOUR_USB_SERIAL getvar serialno` work.
- Obtain Google's USB driver through the [official Android driver page](https://developer.android.com/studio/run/win-usb). The toolkit does not download/install drivers, modify an INF or disable Windows driver-signature enforcement.
- Do not install an arbitrary Rockchip maskrom driver merely because the chip is Rockchip. The tested interface here is fastboot, not a demonstrated loader/maskrom recovery session.

The wizard may stop at its first fastboot query while the driver is being bound. No boot write is issued before the serial/product/partition checks succeed. Once the driver is ready, rerun the same command; the prepared candidate is reused.

## ADB server version conflicts

Another application repeatedly started ADB server protocol version 40 while the newer workspace client expected 41. The conventional client killed/restarted the server, disrupting connection checks.

`x2i.py` implements the necessary localhost ADB server/shell-v2/sync operations and uses the already-running server, rather than repeatedly launching an incompatible client. You must start a server yourself once (`adb start-server`) and deal with actual USB drivers/authorization. It does not bypass on-device authentication or connect to a remote ADB server.

## Stalls and power

`fastboot getvar all` stalled this unit's USB connection, sometimes making the serial display as question marks. It is intentionally never used by the toolkit. Individual `getvar` calls have timeouts.

A physical cold power cycle was needed during the original root experiment. Because the X2i has no battery, disconnecting its power/data USB arrangement may remove all power. Do not do this while flashing. The script cannot power-cycle the device or guarantee that a power cycle fixes every failure.
