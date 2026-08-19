# MiniBig Integration Architecture & Design

This document details the architectural design, component layers, data flows, and state synchronization patterns of the `hass-minibig` Home Assistant custom integration.

---

## 1. Architectural Overview

The integration follows a strict layered architecture separating raw byte manipulation, BLE session management, coordinator aggregation, and entity platforms:

```mermaid
graph TD
    HA_Core[Home Assistant Core] --> Platforms[Entity Platforms]
    Platforms --> ActiveCoord[MiniBigActiveCoordinator]
    HA_BT[HA Bluetooth Scanner] --> PassiveCoord[MiniBigPassiveCoordinator]
    
    ActiveCoord --> SessionMgr[MiniBigConnection Client]
    PassiveCoord --> Parser[minibig_ble.parser]
    
    subgraph Protocol Layer (Zero HA Dependencies)
        SessionMgr --> Writer[minibig_ble.writer]
        SessionMgr --> Devices[minibig_ble.devices]
        Parser
        Writer
        Devices
    end
    
    SessionMgr --> Bleak[Bleak / BLE GATT]
    Bleak --> Peripheral[MiniBig Peripheral Device]
```

---

## 2. Component Layers & Responsibilities

### 2.1 Pure Protocol Core (`custom_components/minibig/minibig_ble/`)
- **`const.py`**: Protocol UUIDs, static XOR key (`PASS_KEY = [0x66, 0x39]`), Opcode enum, StatusCode enum, error message maps.
- **`parser.py`**: Pure function `parse_advertisement` transforming raw manufacturer data into `MiniBigDeviceInfo` without external dependencies.
- **`writer.py`**: Pure frame serialization and deserialization functions (`build_frame`, `build_pub_dps`, `build_read_dps`, `build_legacy_setting`, `parse_response`). Decodes `[dpId, val BE16]` triplets and legacy bitfield acknowledgments.
- **`devices.py`**: Device capability profiles (`PROFILE_WINDOW_OPENER`, `PROFILE_PUSH_MINI_NEW`, `PROFILE_PUSH_MINI_LEGACY`, `PROFILE_SWITCH_MINI`, `PROFILE_UNKNOWN`, `PROFILE_HUB_MINI`).

### 2.2 BLE Transaction Layer (`minibig_ble/client.py`)
- **`MiniBigConnection`**: Manages the GATT connection lifecycle, notification subscription, command queuing, and recovery.
- **Command Coalescing**: Manages a single pending command slot (`_pending_command`). Newer commands supersede older in-flight or waiting commands, raising `MiniBigSupersededError` on superseded tasks.
- **On-demand Sessions & Idle Disconnect**: Establishes connection on demand and automatically disconnects after 30 seconds of inactivity (`idle_disconnect_s`), freeing the single BLE slot for the official app.
- **Single Slot Exhaustion Recovery**: If `BleakOutOfConnectionSlotsError` occurs, automatically purges stale OS connections (`close_stale_connections_by_address`), waits 12 seconds, and retries.

### 2.3 Coordinator Layer (`custom_components/minibig/coordinator.py`)
- **`MiniBigPassiveBluetoothProcessorCoordinator`**: Wraps the HA passive BLE scanner (`BluetoothScanningMode.ACTIVE`) to continuously track advertisement signals (RSSI, pairing mode, firmware revision).
- **`MiniBigActiveCoordinator`**: Coordinates active GATT polling and streaming report aggregation. Skips periodic polling while the device is actively moving.

### 2.4 Entity Platforms
- **`cover.py`**: Window Opener entity with target positioning (0~100%, reported unmodified — verified to match the vendor app's own reading exactly, including non-round endpoints), immediate stop, direction tracking (`is_opening`/`is_closing`), and `RestoreEntity`.
- **`switch.py`**: Power switch for Push/Switch devices with optimistic feedback and readback synchronization.
- **`sensor.py`**: Battery level sensor (`dp10`), diagnostic RSSI sensor, and diagnostic last status sensor.
- **`binary_sensor.py`**: Moving state (active when receiving `REPORT_DPS`), connectivity state (diagnostic), and pairing mode (diagnostic).
- **`button.py`**: Restart, Refresh, and Factory Reset buttons.

---

## 3. Key Design Decisions

### 3.1 Device Info vs. Entities Separation
Firmware version (`fv`), hardware revision (`rev`), and manufacturer name are registered directly to the Home Assistant Device Registry via `DeviceInfo` rather than creating separate cluttering sensor entities.

### 3.2 True Command Coalescing & Exception Safety
When multiple control commands are issued in rapid succession (e.g. Open $\to$ Close $\to$ Stop), pending commands are replaced in the single queue slot and resolved with `MiniBigSupersededError`. Entity platforms handle `MiniBigSupersededError` gracefully by clearing optimistic assumptions without firing error toasts.

### 3.3 Movement Tracking via Streaming Push Packets
While the motor is running, the peripheral pushes live `REPORT_DPS` (opcode 24) packets. The connection manager dispatches these reports immediately, resets the movement idle timer (`movement_idle_s = 3.0s`), and notifies coordinators without aggressive polling.

---

## 4. Integration Custom Services

| Service | Target | Parameters | Description |
|---|---|---|---|
| `minibig.send_raw` | Target Device Picker | `method` (int), `payload` (hex str) | Sends raw opcode frame for diagnostics and testing; fires `minibig_raw_response` event |
| `minibig.publish_dps` | Target Device Picker | `dps` (list of `{"dp_id": int, "value": int}`) | Directly writes DP values to peripheral |
