"""Config flow for CozyLife Local integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

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

        # 如果是第一次进入，尝试发现设备
        if user_input is None:
            self.discovered_devices = await async_discover_devices()
            
            # 如果有发现的设备，显示选择步骤
            if self.discovered_devices:
                return await self.async_step_select_device()
            
            # 如果没有发现设备，直接显示手动输入表单
            return self.async_show_form(
                step_id="manual",
                data_schema=vol.Schema({
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=5555): int,
                })
            )

        # 处理手动输入的表单提交
        try:
            # 验证连接
            from .cozy_client import CozyClient
            
            client = CozyClient(
                host=user_input[CONF_HOST],
                port=user_input.get(CONF_PORT, 5555),
                hass=self.hass
            )
            await client.async_connect()
            await client.async_disconnect()

            # 设置唯一ID
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

        # 显示错误并重新显示表单
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str,
                vol.Optional(CONF_PORT, default=user_input.get(CONF_PORT, 5555)): int,
            }),
            errors=errors
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show discovered devices for selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_option = user_input.get("selected_device")
            
            if selected_option == "manual":
                # 用户选择手动输入
                return await self.async_step_manual()
            
            # 用户选择了一个发现的设备
            self.selected_device = selected_option
            
            # 验证所选设备的连接
            try:
                from .cozy_client import CozyClient
                
                client = CozyClient(
                    host=self.selected_device,
                    port=5555,
                    hass=self.hass
                )
                await client.async_connect()
                await client.async_disconnect()

                # 设置唯一ID
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

        # 创建设备选择表单
        device_options = {
            device: f"CozyLife Device ({device})" 
            for device in self.discovered_devices
        }
        device_options["manual"] = "Manual Entry"
        
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
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show manual device entry form."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # 验证连接
                from .cozy_client import CozyClient
                
                client = CozyClient(
                    host=user_input[CONF_HOST],
                    port=user_input.get(CONF_PORT, 5555),
                    hass=self.hass
                )
                await client.async_connect()
                await client.async_disconnect()

                # 设置唯一ID
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

        # 显示手动输入表单
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=5555): int,
            }),
            errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""