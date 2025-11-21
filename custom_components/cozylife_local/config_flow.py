"""Config flow for CozyLife Local integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .udp_discover import async_discover_devices

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CozyLife Local."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovered_devices: list[str] = []
        self.selected_device: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is None:
            self.discovered_devices = await async_discover_devices()
            
            if self.discovered_devices:
                return await self.async_step_select_device()
            
            return await self.async_step_manual()

        try:
            from .cozy_client import CozyClient
            
            client = CozyClient(
                host=user_input[CONF_HOST],
                port=user_input.get(CONF_PORT, 5555),
                hass=self.hass
            )
            await client.async_connect()
            await client.async_disconnect()

            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"CozyLife ({user_input[CONF_HOST]})",
                data=user_input,
            )

        except ConnectionRefusedError:
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return await self.async_step_manual(errors, user_input)

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show discovered devices for selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_option = user_input.get("selected_device")
            
            if selected_option == "manual":
                return await self.async_step_manual()
            
            self.selected_device = selected_option
            
            try:
                from .cozy_client import CozyClient
                
                client = CozyClient(
                    host=self.selected_device,
                    port=5555,
                    hass=self.hass
                )
                await client.async_connect()
                await client.async_disconnect()

                await self.async_set_unique_id(self.selected_device)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"CozyLife ({self.selected_device})",
                    data={
                        CONF_HOST: self.selected_device,
                        CONF_PORT: 5555
                    },
                )

            except ConnectionRefusedError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # 创建设备选择表单，使用翻译键
        device_options = {
            device: f"CozyLife 设备 ({device})"
            for device in self.discovered_devices
        }
        device_options["manual"] = "手动输入"
        
        schema = vol.Schema({
            vol.Required("selected_device"): vol.In(device_options)
        })

        return self.async_show_form(
            step_id="select_device",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "device_count": str(len(self.discovered_devices))
            }
        )

    async def async_step_manual(
        self, errors: dict[str, str] | None = None, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show manual device entry form."""
        if errors is None:
            errors = {}

        if user_input is not None:
            try:
                from .cozy_client import CozyClient
                
                client = CozyClient(
                    host=user_input[CONF_HOST],
                    port=user_input.get(CONF_PORT, 5555),
                    hass=self.hass
                )
                await client.async_connect()
                await client.async_disconnect()

                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"CozyLife ({user_input[CONF_HOST]})",
                    data=user_input,
                )

            except ConnectionRefusedError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=5555): int,
            }),
            errors=errors
        )