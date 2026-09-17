# Network containment for panel management

## Our chosen deployment policy

For our installation, the owner has chosen network containment rather than changing firmware or removing management features solely because their interfaces lack authentication. The panels are on a dedicated IoT VLAN with client-device isolation. The management policy is:

| Source | Destination | Policy |
|---|---|---|
| Home Assistant and one designated administration PC, on the main LAN | Inventoried panel ADB and HTTP(S) management ports | Allow |
| Every other routed source | Those same panel management ports | Deny |
| Other IoT clients | Panels directly within the IoT VLAN | Enforce client isolation at the wireless/switch layer |
| Panels initiating dashboard, MQTT, DNS, time or camera connections | Their existing services | Preserve the existing policy; this management restriction is not an outbound lockdown |

The router is a MikroTik. Home Assistant, the administration PC and every panel must have stable addresses, such as DHCP reservations. The policy covers the existing Android-panel fleet as well as the X2i. Private addresses, router exports and credentials are deliberately not published.

This documents the selected policy, not a universal ready-to-import firewall configuration or a claim that the toolkit configures a router. Deployment and verification must be performed on the actual network. `x2i.py` does not create firewall rules or change client isolation.

## Why management access needs restriction

The pinned ShellyElevate source listens on TCP 8080 and handles settings reads/writes without an authentication check. Its settings serializer returns preferences without secret redaction, and the WebView endpoint accepts JavaScript injection. Treat access to that service as sensitive access to the panel and potentially its signed-in dashboard session, not merely access to a screen-brightness API. See the pinned [HTTP handler](https://github.com/RapierXbox/ShellyElevate/blob/v3.26170.1522/app/src/main/java/me/rapierxbox/shellyelevatev2/HttpServer.java) and [settings serializer](https://github.com/RapierXbox/ShellyElevate/blob/v3.26170.1522/app/src/main/java/me/rapierxbox/shellyelevatev2/SettingsParser.java).

The current kiosk recipe explicitly enables Elevate's HTTP server. It remains unchanged by this documentation. Establish isolation before exposing that server or entering household credentials. If suitable isolation is unavailable, leave unnecessary management services disabled or select a different deployment approach.

Inventory actual listeners rather than assuming that HTTP means only TCP 80. On the tested X2i, management uses TCP 5555 for ADB and TCP 8080 for Elevate. Other panels or applications may expose additional HTTP(S) management ports, including Fully remote administration if enabled. Do not enable a previously disabled service just to apply a firewall rule.

## RouterOS implementation considerations

- Back up the current configuration privately. Identify the real main-LAN and IoT interfaces, subnets, address reservations, IPv6 configuration and existing rule order before editing. Preserve router administration access and use a recoverable change procedure.
- Use named address lists for the exact panel destinations and the two permitted management sources. Bind source permission to the appropriate ingress network as well as the source address. Do not allow the entire main LAN.
- These are rules for traffic **forwarded to panels**, not router `input` rules. Keep the destination list and management ports narrow so unrelated IoT equipment and panel-initiated HA/MQTT/video connections are unaffected.
- Ensure broad accept rules and FastTrack cannot bypass the new policy. FastTracked connections can remain outside normal filtering until they end; inspect and, where necessary, remove only the affected management connection entries. Do not flush the whole connection table or disable acceleration for unrelated traffic as a shortcut.
- Account for IPv6 separately. IPv4-only filtering is insufficient if panels are reachable over routed IPv6. If management is intentionally IPv4-only, verify there is no IPv6 management path rather than assuming this from an IPv4 address list.
- Same-subnet traffic may never reach the router's IP firewall. Client isolation must cover the relevant APs, wired peers and cross-AP paths; a VLAN name alone does not establish that isolation. Router firewall rules cannot compensate for an unfiltered layer-2 path.
- Do not publish these services through port forwarding or UPnP. An IP allowlist also does not provide application authentication, encryption, or protection against a compromised permitted host. Use dedicated, appropriately restricted HA and MQTT credentials.

MikroTik documents the separate [IPv4/IPv6 filter chains](https://manual.mikrotik.com/docs/firewall-and-quality-of-service/firewall/filter/) and [FastTrack/connection-tracking behavior](https://manual.mikrotik.com/docs/firewall-and-quality-of-service/connection-tracking/).

## Verify the policy

Test fresh connections from both allowed hosts and a non-allowed main-LAN host, and check the corresponding firewall counters. A closed service port is not evidence that a firewall denied it. Verify same-VLAN isolation separately and check any routed IPv6 path. Then confirm the dashboard, MQTT integration, doorbell wake/video and ordinary management still work. Offline panels can be included in the destination list, but their end-to-end tests must wait until they return.

Keep the concrete rules, before/after exports, rollback commands and validation results private. Review the policy whenever panel addresses, management applications, ports, VLANs or administrator devices change.

## Wireless ADB is a separate, explicit decision

After disabling the stock Shelly app, the owner had to manually enable wireless ADB in Android Settings; it was not on by default at that point. Do not assume stock-app removal, successful USB ADB, root, or the kiosk wizard enables network ADB. The toolkit's installation workflow requires a physical USB serial and does not enable wireless ADB.

Enable network ADB only if needed, after establishing the network restrictions, and verify its actual listener and reboot behavior on your firmware. The stock observation `ro.adb.secure=0` describes authentication behavior; it does not prove that a TCP listener is enabled. Root makes an exposed ADB connection especially consequential.

## Firmware and update decisions remain yours

Network containment does not repair the old kernel, supply Android security updates, authenticate Elevate's API, or make the experimental boot replacement recoverable. It is our selected mitigation for a dedicated local appliance, not a recommendation that everyone root, downgrade, freeze firmware, or expose the same services.

Decide independently whether to retain stock firmware, perform this experiment, accept newer firmware, or block the identified updater. `--block-updates` remains explicit and optional, and also blocks security fixes through that path. Evaluate recovery options, network controls, required hardware functions and maintenance needs for your own installation. The warnings in [SAFETY.md](SAFETY.md) still apply.
