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
    
    # 只有在设备类型匹配时才创建实体，无论连接状态如何
    if client.device_type_code == LIGHT_TYPE_CODE:
        async_add_entities([CozyLifeLight(client, entry)])
        _LOGGER.info("Created light entity for %s", client.host)
    else:
        _LOGGER.debug(
            "Not creating light entity for %s: device_type=%s",
            client.host, client.device_type_code
        )


class CozyLifeLight(LightEntity):
    """CozyLife Light entity."""

    def __init__(self, client: CozyClient, entry: ConfigEntry):
        """Initialize with initial state."""
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_light"
        self._attr_has_entity_name = True
        self._attr_translation_key = "cozylife_light"
        
        # 使用缓存的初始状态，避免重复查询
        initial_state = client.initial_state
        self._attr_is_on = initial_state.get(SWITCH, 0) > 0 if initial_state else None
        self._attr_available = client.connected
        self._attr_brightness = None
        self._attr_hs_color = None
        self._attr_color_temp = None
        
        # 如果有初始状态，设置相应的属性
        if initial_state:
            if BRIGHT in initial_state:
                self._attr_brightness = int(initial_state[BRIGHT] / 4)
            if HUE in initial_state and SAT in initial_state:
                self._attr_hs_color = (
                    int(initial_state[HUE]),
                    int(initial_state[SAT] / 10)
                )
            if TEMP in initial_state:
                device_temp = initial_state[TEMP]
                kelvin = 2700 + ((1000 - device_temp) / 1000) * (6500 - 2700)
                self._attr_color_temp = int(1000000 / kelvin)
        
        _LOGGER.debug("Light %s initialized with state: on=%s, brightness=%s", 
                     client.host, self._attr_is_on, self._attr_brightness)
        
        self._attr_supported_color_modes = set()
        self._update_supported_color_modes()

    async def async_added_to_hass(self) -> None:
        """当实体添加到 Home Assistant 时调用."""
        await super().async_added_to_hass()
        # 如果还没有状态，立即触发一次更新
        if self._attr_is_on is None:
            self.hass.async_create_task(self.async_update())

    def _update_supported_color_modes(self):
        """Update supported color modes based on device capabilities."""
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        
        dpid_str_list = [str(dpid) for dpid in self._client.dpid]
        
        if BRIGHT in dpid_str_list:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        
        if TEMP in dpid_str_list:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        
        if HUE in dpid_str_list and SAT in dpid_str_list:
            self._attr_supported_color_modes.add(ColorMode.HS)
        
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
                self._attr_brightness = int(state[BRIGHT] / 4)

            if HUE in state and SAT in state:
                self._attr_hs_color = (
                    int(state[HUE]),
                    int(state[SAT] / 10)
                )

            if TEMP in state:
                device_temp = state[TEMP]
                kelvin = 2700 + ((1000 - device_temp) / 1000) * (6500 - 2700)
                self._attr_color_temp = int(1000000 / kelvin)

            _LOGGER.debug("Light %s state: on=%s, brightness=%s", 
                         self._client.host, self._attr_is_on, self._attr_brightness)

        except Exception as exc:
            _LOGGER.warning("Update failed for light %s: %s", self._client.host, exc)
            self._attr_available = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        payload = {SWITCH: 255}

        if ATTR_BRIGHTNESS in kwargs:
            payload[BRIGHT] = kwargs[ATTR_BRIGHTNESS] * 4

        if ATTR_HS_COLOR in kwargs:
            hue, saturation = kwargs[ATTR_HS_COLOR]
            payload[HUE] = int(hue)
            payload[SAT] = int(saturation * 10)

        if ATTR_COLOR_TEMP in kwargs:
            kelvin = 1000000 / kwargs[ATTR_COLOR_TEMP]
            device_temp = 1000 - ((kelvin - 2700) / (6500 - 2700)) * 1000
            payload[TEMP] = max(0, min(1000, int(device_temp)))

        try:
            success = await self._client.async_control(payload)
            if success:
                await self.async_update()
                _LOGGER.debug("Turned on light %s", self._client.host)
            else:
                _LOGGER.warning("Failed to turn on light %s", self._client.host)
        except Exception as exc:
            _LOGGER.warning("Turn on failed for light %s: %s", self._client.host, exc)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            success = await self._client.async_control({SWITCH: 0})
            if success:
                await self.async_update()
                _LOGGER.debug("Turned off light %s", self._client.host)
            else:
                _LOGGER.warning("Failed to turn off light %s", self._client.host)
        except Exception as exc:
            _LOGGER.warning("Turn off failed for light %s: %s", self._client.host, exc)
            raise