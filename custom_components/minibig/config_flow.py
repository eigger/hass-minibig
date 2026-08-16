"""Config flow and options flow for the MiniBig integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DP_OVERRIDES,
    CONF_KEEP_CONNECTED,
    CONF_POLL_INTERVAL_MIN,
    CONF_POSITION_DP_ID,
    CONF_POWER_DP_ID,
    CONF_RETRY_COUNT,
    DEFAULT_KEEP_CONNECTED,
    DEFAULT_POLL_INTERVAL_MIN,
    DEFAULT_RETRY_COUNT,
    DOMAIN,
)
from .minibig_ble import (
    MiniBigDeviceInfo,
    get_device_profile,
    parse_advertisement,
)

_LOGGER = logging.getLogger(__name__)


class MiniBigConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MiniBig."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._device_info: MiniBigDeviceInfo | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle discovery via Bluetooth."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        dev_info = parse_advertisement(discovery_info)
        if not dev_info:
            return self.async_abort(reason="not_minibig_device")

        if not dev_info.supported or dev_info.d_type == 2:
            _LOGGER.info(
                "HubMini device (%s) detected. HubMini is a gateway and not supported directly",
                discovery_info.address,
            )
            return self.async_abort(reason="hubmini_not_supported")

        self._discovery_info = discovery_info
        self._device_info = dev_info

        profile = get_device_profile(dev_info)
        title = f"{profile.model_name} {dev_info.address[-8:]}"
        self.context["title_placeholders"] = {"name": title}

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        assert self._device_info is not None
        dev_info = self._device_info
        profile = get_device_profile(dev_info)
        title = f"{profile.model_name} {dev_info.address[-8:]}"

        if user_input is not None:
            return self.async_create_entry(
                title=title,
                data={
                    CONF_ADDRESS: dev_info.address,
                },
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": title,
                "address": dev_info.address,
                "model": profile.model_name,
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual user discovery."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            # Find matching discovered device info
            for discovery in async_discovered_service_info(self.hass):
                if discovery.address.upper() == address.upper():
                    dev_info = parse_advertisement(discovery)
                    if dev_info:
                        if not dev_info.supported or dev_info.d_type == 2:
                            return self.async_abort(reason="hubmini_not_supported")
                        profile = get_device_profile(dev_info)
                        title = f"{profile.model_name} {dev_info.address[-8:]}"
                        return self.async_create_entry(
                            title=title,
                            data={CONF_ADDRESS: dev_info.address},
                        )

            return self.async_create_entry(
                title=f"MiniBig {address[-8:]}",
                data={CONF_ADDRESS: address},
            )

        discovered_devices: dict[str, str] = {}
        for discovery in async_discovered_service_info(self.hass):
            dev_info = parse_advertisement(discovery)
            if dev_info and dev_info.supported and dev_info.d_type != 2:
                profile = get_device_profile(dev_info)
                discovered_devices[dev_info.address] = f"{profile.model_name} ({dev_info.address})"

        if not discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(discovered_devices),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowWithReload:
        """Get the options flow for this handler."""
        return MiniBigOptionsFlowHandler(config_entry)


class MiniBigOptionsFlowHandler(OptionsFlowWithReload):
    """Handle MiniBig options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_KEEP_CONNECTED,
                        default=options.get(CONF_KEEP_CONNECTED, DEFAULT_KEEP_CONNECTED),
                    ): bool,
                    vol.Optional(
                        CONF_POLL_INTERVAL_MIN,
                        default=options.get(CONF_POLL_INTERVAL_MIN, DEFAULT_POLL_INTERVAL_MIN),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0, max=1440, step=1, mode=selector.NumberSelectorMode.BOX
                        )
                    ),
                    vol.Optional(
                        CONF_RETRY_COUNT,
                        default=options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=5, step=1, mode=selector.NumberSelectorMode.BOX
                        )
                    ),
                    vol.Optional(
                        CONF_POWER_DP_ID,
                        description={"suggested_value": options.get(CONF_POWER_DP_ID)},
                    ): vol.Any(None, vol.Coerce(int)),
                    vol.Optional(
                        CONF_POSITION_DP_ID,
                        description={"suggested_value": options.get(CONF_POSITION_DP_ID)},
                    ): vol.Any(None, vol.Coerce(int)),
                    vol.Optional(
                        CONF_DP_OVERRIDES,
                        description={"suggested_value": options.get(CONF_DP_OVERRIDES)},
                    ): selector.ObjectSelector(),
                }
            ),
        )
