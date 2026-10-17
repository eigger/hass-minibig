# MiniBig BLE for Home Assistant

<!-- hass-standards:badges:start -->
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square)](#installation)
[![Release](https://img.shields.io/github/v/release/eigger/hass-minibig?style=flat-square)](https://github.com/eigger/hass-minibig/releases)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.8.0-41BDF5?style=flat-square)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-minibig/tests.yml?branch=main&style=flat-square&label=Tests)](https://github.com/eigger/hass-minibig/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-minibig/validate.yml?branch=main&style=flat-square&label=Validate)](https://github.com/eigger/hass-minibig/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-minibig?style=flat-square)](LICENSE)
[![Analytics reporting installs](https://img.shields.io/badge/dynamic/json?style=flat-square&color=41BDF5&label=Usage&query=%24.minibig.total&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json)](https://analytics.home-assistant.io/)
<!-- hass-standards:badges:end -->

**English** | [한국어](README.ko.md)

A HACS custom integration for local Bluetooth GATT control of MiniBig window openers and PushMini/SwitchMini devices, without a cloud account or HubMini.

## Devices and features

- Window openers: position, stop, movement reports and battery.
- PushMini: modern and legacy profiles; capabilities depend on the profile. SwitchMini power control may require a confirmed DP override.
- Diagnostic sensors report connection, range, failures and connection duration. Unknown devices expose only supported profile capabilities; HubMini is rejected.

See [device profiles, options and protocol details](docs/usage.md). Legacy PushMini has no battery DP; firmware variants are not interchangeable.

## Requirements

Home Assistant **2025.8.0 or newer** and a connectable Bluetooth adapter/proxy in range. Home Assistant installs `blesession` automatically. Complete initial mounting, direction and travel-limit calibration with the vendor app, then disconnect the app before HA control.

For proxy configuration and recommended hardware, use the [shared Bluetooth guide (Korean)](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md). Discovery scans and active GATT connections are separate requirements.

## Installation

1. In HACS, add `https://github.com/eigger/hass-minibig` as a custom repository, category **Integration**.
2. Download **MiniBig**, then restart Home Assistant. Alternatively copy `custom_components/minibig` into `<config_dir>/custom_components/` and restart.
3. Power on the device nearby and configure the Bluetooth discovery notification, or add **MiniBig** under **Settings → Devices & services**.
4. Use the created cover/switch controls. For example, send `cover.stop_cover` to the window entity from **Developer Tools → Actions** to stop movement.

## Important limits

Keep the opening clear and supervise physical window/motor commands. Raw commands, factory reset and unknown DP overrides can change calibration or move hardware; use them only with a confirmed model-specific mapping. **Keep Connected** is off by default; enabling it occupies the device's BLE connection and may block the phone app and increase battery use. Battery reports are profile-dependent.

Historical CLWM-B06 hardware observations are preserved in the detailed guide. This standards adoption does **not** constitute new physical-device, proxy-board or HA frontend testing. Usage counts are opted-in HA Analytics installations; unavailable data does not mean zero installs.

## Documentation

- [Usage, profiles, options and raw actions](docs/usage.md) · [한국어](docs/usage.ko.md)
- [Bluetooth troubleshooting and safe reporting](docs/troubleshooting.md) · [한국어](docs/troubleshooting.ko.md)
- [BLE protocol](docs/BLE_PROTOCOL.md) · [Architecture](docs/ARCHITECTURE.md)
- [Development, real HA tests and dependencies (Korean)](docs/development.md)
- [Standards and verification record](STANDARDS.md)

## Support and license

Report bugs in [Issues](https://github.com/eigger/hass-minibig/issues); use [Discussions](https://github.com/eigger/hass-minibig/discussions) for questions and proposals. Remove addresses, device IDs, raw event payloads and sensitive physical-state details before posting logs.

Released under the [MIT License](LICENSE).
