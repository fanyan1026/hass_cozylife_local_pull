"""The CozyLife Local integration."""
"""The CozyLife Local integration."""
from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .cozy_client import CozyClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [
    Platform.LIGHT,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CozyLife Local from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = CozyClient(
        host=entry.data["host"],
        port=entry.data.get("port", 5555),
        hass=hass  # 传递 hass 对象
    )

    try:
        await client.async_connect()
    except Exception as exc:
        _LOGGER.error("Failed to connect to device: %s", exc)
        raise ConfigEntryNotReady from exc

    hass.data[DOMAIN][entry.entry_id] = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        client = hass.data[DOMAIN].pop(entry.entry_id)
        await client.async_disconnect()

    return unload_ok