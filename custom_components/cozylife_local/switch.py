"""Switch platform for CozyLife Local integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SWITCH_TYPE_CODE, SWITCH
from .cozy_client import CozyClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch platform."""
    client: CozyClient = hass.data[DOMAIN][entry.entry_id]
    
    # 只有在设备类型匹配时才创建实体，无论连接状态如何
    if client.device_type_code == SWITCH_TYPE_CODE:
        async_add_entities([CozyLifeSwitch(client, entry)])
        _LOGGER.info("Created switch entity for %s", client.host)
    else:
        _LOGGER.debug(
            "Not creating switch entity for %s: device_type=%s",
            client.host, client.device_type_code
        )


class CozyLifeSwitch(SwitchEntity):
    """CozyLife Switch entity."""

    def __init__(self, client: CozyClient, entry: ConfigEntry):
        """Initialize with initial state."""
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_switch"
        self._attr_has_entity_name = True
        self._attr_translation_key = "cozylife_switch"
        
        # 使用缓存的初始状态，避免重复查询
        initial_state = client.initial_state
        self._attr_is_on = initial_state.get(SWITCH, 0) > 0 if initial_state else None
        self._attr_available = client.connected
        _LOGGER.debug("Switch %s initialized with state: %s", client.host, self._attr_is_on)

    async def async_added_to_hass(self) -> None:
        """当实体添加到 Home Assistant 时调用."""
        await super().async_added_to_hass()
        # 如果还没有状态，立即触发一次更新
        if self._attr_is_on is None:
            self.hass.async_create_task(self.async_update())

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
            _LOGGER.debug("Switch %s state: %s", self._client.host, self._attr_is_on)

        except Exception as exc:
            _LOGGER.warning("Update failed for switch %s: %s", self._client.host, exc)
            self._attr_available = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            success = await self._client.async_control({SWITCH: 255})
            if success:
                await self.async_update()
                _LOGGER.debug("Turned on switch %s", self._client.host)
            else:
                _LOGGER.warning("Failed to turn on switch %s", self._client.host)
        except Exception as exc:
            _LOGGER.warning("Turn on failed for switch %s: %s", self._client.host, exc)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            success = await self._client.async_control({SWITCH: 0})
            if success:
                await self.async_update()
                _LOGGER.debug("Turned off switch %s", self._client.host)
            else:
                _LOGGER.warning("Failed to turn off switch %s", self._client.host)
        except Exception as exc:
            _LOGGER.warning("Turn off failed for switch %s: %s", self._client.host, exc)
            raise