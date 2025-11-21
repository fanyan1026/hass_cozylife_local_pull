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
    
    if client.device_type_code == SWITCH_TYPE_CODE:
        async_add_entities([CozyLifeSwitch(client, entry)])


class CozyLifeSwitch(SwitchEntity):
    """CozyLife Switch entity."""

    def __init__(self, client: CozyClient, entry: ConfigEntry):
        """Initialize."""
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_switch"
        self._attr_name = f"CozyLife Switch ({client.host})"
        self._attr_is_on = None
        self._attr_available = False

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

        except Exception as exc:
            _LOGGER.error("Update failed: %s", exc)
            self._attr_available = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self._client.async_control({SWITCH: 255})
            # 更新状态
            await self.async_update()
        except Exception as exc:
            _LOGGER.error("Turn on failed: %s", exc)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self._client.async_control({SWITCH: 0})
            # 更新状态
            await self.async_update()
        except Exception as exc:
            _LOGGER.error("Turn off failed: %s", exc)
            raise