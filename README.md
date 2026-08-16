# MiniBig BLE for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/eigger/hass-minibig.svg)](https://github.com/eigger/hass-minibig/releases)
[![HACS Default](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Home Assistant custom integration to directly control **MiniBig** Bluetooth Low Energy (BLE) devices locally without cloud dependencies.

---

## Supported Devices

| Device | Type Identifier | Features | Supported Platforms |
|---|---|---|---|
| **Window Opener** (창문 오프너) | Generic (`d_type != 1, 2`) | Target position (0~100%), stop, battery, real-time movement streaming | `cover`, `sensor`, `binary_sensor`, `button` |
| **PushMini (New)** (신형 푸시미니) | `d_type = 1` | On/Off toggle (`dp0`), battery (`dp10`), restart, factory reset | `switch`, `sensor`, `binary_sensor`, `button` |
| **PushMini (Legacy)** (구형 푸시미니) | `d_type = 1` + legacy condition | Action / Setting bitfields, restart, factory reset | `switch`, `sensor`, `binary_sensor`, `button` |
| **SwitchMini** (스위치미니) | `d_type = 1` / Switch | On/Off toggle, battery, custom DP ID injection | `switch`, `sensor`, `binary_sensor`, `button` |
| **HubMini** (허브미니) | `d_type = 2` | External gateway for other platforms — **Not needed** in HA | *Explicitly rejected* (HA connects directly via BLE) |

---

## Key Features

- **100% Local GATT Control**: Fast and direct Bluetooth GATT transactions without account login or cloud dependencies.
- **On-demand Sessions with Idle Disconnect**: Establishes connection on demand and automatically disconnects after 30 seconds of inactivity to free the BLE slot for the official app and conserve battery.
- **End-stop Snapping**: Automatically normalizes window opener positions (<= 2% -> 0%, >= 98% -> 100%).
- **Active Streaming Movement Tracking**: Uses `REPORT_DPS` (opcode 24) live push packets to track moving state smoothly without excessive polling.
- **Command Coalescing**: Consecutive commands sent during connection setup or in-flight execution automatically overwrite older pending commands so only the latest intended state is dispatched to the motor.
- **Slot Exhaustion Recovery**: Automatically handles stale connections and single-slot limitations with retry and recovery logic.

---

## Installation

### Via HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Click the top-right menu (three dots) -> **Custom repositories**.
3. Add repository URL: `https://github.com/eigger/hass-minibig` with Category: **Integration**.
4. Search for **MiniBig** in HACS and click **Download**.
5. Restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/minibig` folder into your Home Assistant `<config_dir>/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

When a MiniBig device is powered on nearby, Home Assistant Bluetooth will automatically discover it. Click **Configure** on the notification to add it.

### Options

In the integration device settings, click **Configure** to adjust:

- **Keep Connected** (`keep_connected`): Keeps a persistent BLE connection.
  > **Note**: Enabling this prevents the official smartphone app from connecting and increases device battery drain. Default is **Disabled**.
- **Polling Interval** (`poll_interval_min`): Background status polling interval in minutes (default: 30m, set to `0` to disable periodic polling). Polling is skipped while the device is actively moving.
- **Connection Retry Attempts** (`retry_count`): Number of BLE connection attempts upon initial failure (default: 3).
- **Custom DP IDs**: Option to inject custom `power_dp_id` or `position_dp_id` for unconfirmed hardware variants or testing.

---

## Discovering Custom or Unknown DP IDs

To discover active DP IDs on newer or unlisted device variants:

1. Call the `minibig.send_raw` service from **Developer Tools -> Actions**:
   ```yaml
   action: minibig.send_raw
   target:
     device_id: <YOUR_DEVICE_ID>
   data:
     method: 43 # 43 is READ_DPS
     payload: ""
   ```
2. Check the response in the Home Assistant logs or listen for the `minibig_raw_response` event under **Developer Tools -> Events**.
3. The response contains repeated `[dpId (1 byte)][value (2 bytes BE)]` triplets showing all active DPs on the device.

---

## Technical Documentation

- [BLE Protocol Specification](docs/BLE_PROTOCOL.md): Complete technical specification of GATT services, packet layouts, encryption key, and opcodes.
- [Architecture & Design](docs/ARCHITECTURE.md): Component layering, coordinator state flows, and transaction management design.

---

## Debug Logging

To enable verbose protocol debugging, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.minibig: debug
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
