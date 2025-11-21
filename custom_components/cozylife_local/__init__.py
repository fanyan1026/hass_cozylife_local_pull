"""The CozyLife Local integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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

    # 检查是否正在重新加载，如果是则重用现有连接
    if entry.entry_id in hass.data[DOMAIN]:
        _LOGGER.debug("Reusing existing client for reloaded entry %s", entry.entry_id)
        client = hass.data[DOMAIN][entry.entry_id]
        
        # 如果客户端已连接，直接设置平台
        if client.connected:
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
            return True
        else:
            # 如果连接断开，尝试重新连接
            _LOGGER.debug("Client disconnected, reconnecting for entry %s", entry.entry_id)
    else:
        # 新条目，创建新客户端
        client = CozyClient(
            host=entry.data["host"],
            port=entry.data.get("port", 5555),
            hass=hass
        )
        hass.data[DOMAIN][entry.entry_id] = client

    # 立即连接设备
    try:
        await client.async_connect()
        _LOGGER.info("Successfully connected to device %s", entry.data["host"])
    except Exception as exc:
        _LOGGER.error("Failed to connect to device %s: %s", entry.data["host"], exc)
        # 即使连接失败也继续设置，让实体处理不可用状态
        _LOGGER.warning("Device connection failed, entities will start as unavailable")

    # 存储客户端并设置平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # 先卸载平台
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # 注意：我们不在这里断开连接，以便重新加载时可以重用
        _LOGGER.debug("Unloaded platforms for entry %s, keeping connection for potential reload", entry.entry_id)
        
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    # 只有在完全删除条目时才断开连接
    client = hass.data[DOMAIN].pop(entry.entry_id, None)
    if client:
        await client.async_disconnect()
        _LOGGER.info("Removed CozyLife Local entry for %s", entry.data["host"])


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle reload of an entry."""
    _LOGGER.debug("Reloading entry %s", entry.entry_id)
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)