# MiniBig Bluetooth troubleshooting

[한국어](troubleshooting.ko.md) · [README](../README.md) · [Usage](usage.md)

## Prepare the right model

Use the actual advertisement/profile, firmware and hardware revision when reporting a problem. Window Opener, modern/legacy PushMini, SwitchMini and HubMini have different capabilities. Legacy PushMini has no battery DP. Unknown profile devices do not acquire guessed control DPs. HubMini is not supported or required. Existing CLWM-B06 observations in [the protocol reference](BLE_PROTOCOL.md) are historical; no new hardware test is claimed here.

For a window opener, finish vendor-app mounting, opening direction and travel-limit calibration before trying HA. The integration does not identify every model's installation/calibration DP. Do not guess override IDs to solve a connectivity issue. Keep the travel path clear, supervise movement, and avoid restart/factory reset/raw writes on an occupied opening. Power and charge the device as its own manual requires; no universal pairing, bonding or reset procedure is assumed.

## Discovery and connection are separate

Follow the [Bluetooth proxy setup](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md). Its XIAO W5500 and USB-A AtomS3U recommendations are shared guidance, not hardware verified with this integration during adoption.

1. Check that HA's Bluetooth integration and the intended local adapter/proxy are online, powered and in range. Compare proximity to the device; metal window frames and proxy network interruptions affect reception.
2. Check advertisements first. The passive coordinator requests HA `BluetoothScanningMode.ACTIVE`; an active scan requests advertising scan responses. This is distinct from ESPHome proxy `bluetooth_proxy.active`, which enables active GATT connections. Seeing an advertisement does not prove that a proxy has an available connectable GATT route.
3. Disconnect the vendor phone app/other BLE central and bring the powered device nearby. Device wake/pairing procedures vary by model; follow its manual and report the observed pairing diagnostic rather than applying an ESL procedure.
4. Check available connection slots and other connected devices. **Keep Connected** defaults to false; enabled sessions can occupy the device's single BLE connection and prevent app use. Normal sessions disconnect after the configured idle period (default 30 seconds); a reported disconnected link between commands can be normal.
5. Retry a normal entity operation after removing the competing connection. Do not repeatedly write unknown raw commands or restart HA as a substitute for checking radio routing and slot availability.

## Interpret actual diagnostic entities

- **In range** follows advertisement presence; **Connected** follows the active GATT link. Neither proves that an individual command succeeded.
- **Moving** is driven by movement reports. Polling is skipped during movement. `poll_interval_min=0` disables periodic polling; it does not disable user actions or pushed reports.
- **Last Failure**, **Error Count** and **Connection Duration** report BLE session outcomes. Failure attributes include operation/stage, likely cause, adapter/proxy routing (`via`, RSSI, paths), timings and error text. Out-of-range status polls are intentionally not counted as command failures.
- Model/protocol mapping issues differ from radio failures. Preserve the actual reported position, including non-round endpoints; do not assume 97% is a transport failure. `power_dp_id`, `position_dp_id` and named `dp_overrides` need confirmed model mappings. Select choices also need known raw enum maps, so an override alone does not make all optional entities appear.

For confirmed DP exploration only, see [the raw action example](usage.md#discovering-custom-or-unknown-dp-ids). `minibig.send_raw` accepts `device_id` inside **data**, not a HA target selector. Listen to **Developer Tools → Events → `minibig_raw_response`** for the response. The event deliberately contains device ID/address, method, status, raw data and success status. Receiving an event confirms a response, not physical calibration correctness. Use normal entity actions for routine control.

## Safe reports

Enable `custom_components.minibig: debug` only while reproducing the issue, then disable it. Debug protocol logs, BLE failure sensor attributes and raw response events may reveal Bluetooth addresses, proxy addresses/names/routes, identity bytes, physical positions, raw packets and session timing. These local diagnostic values are not automatically safe to post publicly.

Before opening [an issue](https://github.com/eigger/hass-minibig/issues), remove/redact addresses, device/entry IDs, proxy names/IPs, raw payloads and private state details. Preserve opcode, error type, stage and sanitized timing if useful. Include HA/integration/blesession versions, device model/firmware, local adapter versus proxy model/firmware, Keep Connected and polling settings, reproducible steps, and whether discovery, GATT connection, command response or physical movement failed. Do not attach your entire HA configuration or unsanitized event dump. Never publicly post credentials or keys.

Automated real HA tests validate integration behavior using external BLE boundaries. They do not verify physical mechanics, every firmware/model, a new proxy board or the frontend UI.
