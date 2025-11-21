"""Async TCP client for CozyLife devices."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.exceptions import HomeAssistantError

from .const import (
    SWITCH_TYPE_CODE,
    LIGHT_TYPE_CODE,
    SWITCH,
    TEMP,
    BRIGHT,
    HUE,
    SAT,
)
from .utils import get_pid_list, get_sn

_LOGGER = logging.getLogger(__name__)

CMD_INFO = 0
CMD_QUERY = 2
CMD_SET = 3


class CozyClient:
    """Async TCP client for CozyLife devices."""

    def __init__(self, host: str, port: int = 5555, hass=None):
        self.host = host
        self.port = port
        self.hass = hass
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._device_id: str | None = None
        self._pid: str | None = None
        self._device_type_code: str | None = None
        self._device_model_name: str | None = None
        self._dpid: list = []
        self._sn: str | None = None
        self._lock = asyncio.Lock()
        # 缓存初始状态，避免重复查询
        self._initial_state: dict = {}
        # 跟踪连接尝试
        self._connection_attempts = 0

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def device_id(self) -> str | None:
        return self._device_id

    @property
    def device_type_code(self) -> str | None:
        return self._device_type_code

    @property
    def device_model_name(self) -> str | None:
        return self._device_model_name

    @property
    def dpid(self) -> list:
        return self._dpid

    @property
    def initial_state(self) -> dict:
        """返回缓存的初始状态"""
        return self._initial_state

    async def async_connect(self) -> None:
        """Async connect to device and get initial state."""
        if self._connected:
            _LOGGER.debug("Already connected to %s:%s", self.host, self.port)
            return

        self._connection_attempts += 1
        _LOGGER.debug("Connection attempt %d to %s:%s", self._connection_attempts, self.host, self.port)

        try:
            # 建立 TCP 连接
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )
            self._connected = True
            self._connection_attempts = 0  # 重置尝试次数
            _LOGGER.info("Connected to %s:%s", self.host, self.port)

            # 立即获取设备信息和初始状态
            await self._async_get_basic_device_info()
            # 获取初始设备状态
            self._initial_state = await self.async_query()
            _LOGGER.debug("Retrieved initial state for %s: %s", self.host, self._initial_state)

        except asyncio.TimeoutError:
            _LOGGER.warning("Connection timeout to %s:%s", self.host, self.port)
            await self._safe_disconnect()
            raise ConnectionRefusedError(f"Connection timeout to {self.host}:{self.port}")
        except Exception as exc:
            _LOGGER.warning("Connection failed to %s:%s: %s", self.host, self.port, exc)
            await self._safe_disconnect()
            raise HomeAssistantError(f"Failed to connect: {exc}")

    async def _safe_disconnect(self) -> None:
        """Safely disconnect from device."""
        self._connected = False
        if self._writer:
            self._writer.close()
            try:
                await asyncio.wait_for(self._writer.wait_closed(), timeout=2.0)
            except asyncio.TimeoutError:
                pass
            self._writer = None
            self._reader = None

    async def async_disconnect(self) -> None:
        """Async disconnect from device."""
        await self._safe_disconnect()
        _LOGGER.debug("Disconnected from %s:%s", self.host, self.port)

    async def _async_get_basic_device_info(self) -> None:
        """Get basic device information needed for platform setup."""
        try:
            await self._async_send_command(CMD_INFO, {})
            response = await self._async_receive()
            
            if not response or 'msg' not in response:
                _LOGGER.warning("Invalid device info response from %s", self.host)
                return

            msg = response['msg']
            self._device_id = msg.get('did')
            self._pid = msg.get('pid')

            if not self._device_id or not self._pid:
                _LOGGER.warning("Missing device ID or PID from %s", self.host)
                return

            # 获取设备类型信息
            await self._async_get_device_type()

        except Exception as exc:
            _LOGGER.warning("Failed to get basic device info from %s: %s", self.host, exc)

    async def _async_get_device_type(self) -> None:
        """Get device type information."""
        try:
            # 使用同步方式获取设备类型
            if self.hass:
                pid_list = await self.hass.async_add_executor_job(get_pid_list)
            else:
                pid_list = get_pid_list()

            for item in pid_list:
                for item1 in item.get('m', []):
                    if item1.get('pid') == self._pid:
                        self._device_model_name = item1.get('n', 'Unknown')
                        self._dpid = item1.get('dpid', [])
                        self._device_type_code = item.get('c', LIGHT_TYPE_CODE)
                        _LOGGER.info(
                            "Device info: %s, type: %s", 
                            self._device_model_name, 
                            self._device_type_code
                        )
                        return

            _LOGGER.warning("No device model found for PID: %s", self._pid)

        except Exception as exc:
            _LOGGER.warning("Failed to get device type for %s: %s", self.host, exc)

    def _get_package(self, cmd: int, payload: dict) -> bytes:
        """Create command package."""
        self._sn = get_sn()
        
        if cmd == CMD_SET:
            message = {
                'pv': 0,
                'cmd': cmd,
                'sn': self._sn,
                'msg': {
                    'attr': [int(item) for item in payload.keys()],
                    'data': payload,
                }
            }
        elif cmd == CMD_QUERY:
            message = {
                'pv': 0,
                'cmd': cmd,
                'sn': self._sn,
                'msg': {
                    'attr': [0],
                }
            }
        elif cmd == CMD_INFO:
            message = {
                'pv': 0,
                'cmd': cmd,
                'sn': self._sn,
                'msg': {}
            }
        else:
            raise ValueError(f"Invalid command: {cmd}")

        return json.dumps(message, separators=(',', ':')).encode('utf-8') + b"\r\n"

    async def _async_send_command(self, cmd: int, payload: dict) -> None:
        """Send command to device."""
        if not self._connected:
            raise HomeAssistantError("Not connected to device")

        data = self._get_package(cmd, payload)
        _LOGGER.debug("Sending command to %s: %s", self.host, data.decode('utf-8').strip())
        
        self._writer.write(data)
        await self._writer.drain()

    async def _async_receive(self) -> dict | None:
        """Receive response from device."""
        if not self._connected:
            return None

        try:
            data = await asyncio.wait_for(
                self._reader.readuntil(b"\r\n"),
                timeout=3.0
            )
            response = json.loads(data.decode('utf-8').strip())
            _LOGGER.debug("Received response from %s: %s", self.host, response)
            return response
        except asyncio.TimeoutError:
            _LOGGER.debug("Receive timeout from %s", self.host)
            return None
        except Exception as exc:
            _LOGGER.debug("Receive error from %s: %s", self.host, exc)
            return None

    async def async_query(self) -> dict:
        """Query device state."""
        if not self._connected:
            return {}
            
        async with self._lock:
            try:
                await self._async_send_command(CMD_QUERY, {})
                
                for _ in range(3):
                    response = await self._async_receive()
                    if response and response.get('sn') == self._sn:
                        msg = response.get('msg', {})
                        return msg.get('data', {})
                
                _LOGGER.debug("No valid response from %s after 3 attempts", self.host)
                return {}
            except Exception as exc:
                _LOGGER.debug("Query failed for %s: %s", self.host, exc)
                return {}

    async def async_control(self, payload: dict) -> bool:
        """Send control command to device."""
        if not self._connected:
            return False
            
        async with self._lock:
            try:
                await self._async_send_command(CMD_SET, payload)
                return True
            except Exception as exc:
                _LOGGER.debug("Control failed for %s: %s", self.host, exc)
                return False