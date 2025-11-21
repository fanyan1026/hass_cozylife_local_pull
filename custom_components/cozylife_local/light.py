"""Light platform for CozyLife Local integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LIGHT_TYPE_CODE, SWITCH, TEMP, BRIGHT, HUE, SAT
from .cozy_client import CozyClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light platform."""
    client: CozyClient = hass.data[DOMAIN][entry.entry_id]
    
    if client.device_type_code == LIGHT_TYPE_CODE:
        async_add_entities([CozyLifeLight(client, entry)])


class CozyLifeLight(LightEntity):
    """CozyLife Light entity."""

    def __init__(self, client: CozyClient, entry: ConfigEntry):
        """Initialize."""
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_light"
        self._attr_name = f"CozyLife Light ({client.host})"
        self._attr_is_on = None
        self._attr_available = False
        self._attr_brightness = None
        self._attr_hs_color = None
        self._attr_color_temp = None
        
        # 动态设置支持的颜色模式
        self._attr_supported_color_modes = set()
        self._update_supported_color_modes()

    def _update_supported_color_modes(self):
        """Update supported color modes based on device capabilities."""
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        
        # 检查设备支持的 DPID
        dpid_str_list = [str(dpid) for dpid in self._client.dpid]
        
        if BRIGHT in dpid_str_list:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        
        if TEMP in dpid_str_list:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        
        if HUE in dpid_str_list and SAT in dpid_str_list:
            self._attr_supported_color_modes.add(ColorMode.HS)
        
        # 设置默认颜色模式
        if ColorMode.HS in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.HS
        elif ColorMode.COLOR_TEMP in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif ColorMode.BRIGHTNESS in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._client.connected and self._attr_available

    async def async_update(self) -> None:
        """Update entity state."""
        if not self._client.connected:
            self._attr_available = False
            return

        try:
            state = await self._client.async_query()
            if not state:
                self._attr_available = False
                return

            self._attr_available = True
            self._attr_is_on = state.get(SWITCH, 0) > 0

            if BRIGHT in state:
                self._attr_brightness = int(state[BRIGHT] / 4)  # 0-1000 to 0-255

            if HUE in state and SAT in state:
                self._attr_hs_color = (
                    int(state[HUE]),
                    int(state[SAT] / 10)  # 0-1000 to 0-100
                )

            if TEMP in state:
                # Convert device temp (0-1000) to color temp (mireds)
                device_temp = state[TEMP]
                # 将设备色温值转换为开尔文，然后转换为 mireds
                kelvin = 2700 + ((1000 - device_temp) / 1000) * (6500 - 2700)
                self._attr_color_temp = int(1000000 / kelvin)  # 转换为 mireds

        except Exception as exc:
            _LOGGER.error("Update failed: %s", exc)
            self._attr_available = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        payload = {SWITCH: 255}

        if ATTR_BRIGHTNESS in kwargs:
            payload[BRIGHT] = kwargs[ATTR_BRIGHTNESS] * 4  # 0-255 to 0-1000

        if ATTR_HS_COLOR in kwargs:
            hue, saturation = kwargs[ATTR_HS_COLOR]
            payload[HUE] = int(hue)
            payload[SAT] = int(saturation * 10)  # 0-100 to 0-1000

        if ATTR_COLOR_TEMP in kwargs:
            # 将 mireds 转换为设备色温值
            kelvin = 1000000 / kwargs[ATTR_COLOR_TEMP]
            device_temp = 1000 - ((kelvin - 2700) / (6500 - 2700)) * 1000
            payload[TEMP] = max(0, min(1000, int(device_temp)))

        try:
            await self._client.async_control(payload)
            # 更新状态
            await self.async_update()
        except Exception as exc:
            _LOGGER.error("Turn on failed: %s", exc)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self._client.async_control({SWITCH: 0})
            # 更新状态
            await self.async_update()
        except Exception as exc:
            _LOGGER.error("Turn off failed: %s", exc)
            raise