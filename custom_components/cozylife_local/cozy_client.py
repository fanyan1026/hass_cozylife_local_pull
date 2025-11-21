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
        self.hass = hass  # 保存 hass 引用
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._device_id: str | None = None
        self._pid: str | None = None
        self._device_type_code: str | None = None
        self._device_model_name: str | None = None
        self._dpid: list = []
        self._sn: str | None = None

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

    async def async_connect(self) -> None:
        """Async connect to device."""
        if self._connected:
            return

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )
            self._connected = True
            _LOGGER.info(f"Connected to {self.host}:{self.port}")

            # 获取设备信息
            await self._async_device_info()

        except asyncio.TimeoutError:
            raise ConnectionRefusedError(f"Connection timeout to {self.host}:{self.port}")
        except Exception as exc:
            raise HomeAssistantError(f"Failed to connect: {exc}")

    async def async_disconnect(self) -> None:
        """Async disconnect from device."""
        self._connected = False
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def _async_device_info(self) -> None:
        """Get device information."""
        try:
            await self._async_send_command(CMD_INFO, {})
            response = await self._async_receive()
            
            if not response or 'msg' not in response:
                _LOGGER.error("Invalid device info response")
                return

            msg = response['msg']
            self._device_id = msg.get('did')
            self._pid = msg.get('pid')

            if not self._device_id or not self._pid:
                _LOGGER.error("Missing device ID or PID")
                return

            # 获取设备型号信息 - 使用 hass 执行同步函数
            if self.hass:
                pid_list = await self.hass.async_add_executor_job(get_pid_list)
                for item in pid_list:
                    for item1 in item.get('m', []):
                        if item1.get('pid') == self._pid:
                            self._device_model_name = item1.get('n', 'Unknown')
                            self._dpid = item1.get('dpid', [])
                            self._device_type_code = item.get('c', LIGHT_TYPE_CODE)
                            _LOGGER.info(f"Device info: {self._device_model_name}, type: {self._device_type_code}")
                            return
            else:
                # 如果没有 hass，直接调用同步函数（在配置流中）
                pid_list = get_pid_list()
                for item in pid_list:
                    for item1 in item.get('m', []):
                        if item1.get('pid') == self._pid:
                            self._device_model_name = item1.get('n', 'Unknown')
                            self._dpid = item1.get('dpid', [])
                            self._device_type_code = item.get('c', LIGHT_TYPE_CODE)
                            _LOGGER.info(f"Device info: {self._device_model_name}, type: {self._device_type_code}")
                            return

        except Exception as exc:
            _LOGGER.error(f"Failed to get device info: {exc}")

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
        _LOGGER.debug(f"Sending command: {data.decode('utf-8').strip()}")
        
        self._writer.write(data)
        await self._writer.drain()

    async def _async_receive(self) -> dict | None:
        """Receive response from device."""
        if not self._connected:
            return None

        try:
            data = await asyncio.wait_for(
                self._reader.readuntil(b"\r\n"),
                timeout=5.0
            )
            response = json.loads(data.decode('utf-8').strip())
            _LOGGER.debug(f"Received response: {response}")
            return response
        except asyncio.TimeoutError:
            _LOGGER.error("Receive timeout")
            return None
        except Exception as exc:
            _LOGGER.error(f"Receive error: {exc}")
            return None

    async def async_query(self) -> dict:
        """Query device state."""
        await self._async_send_command(CMD_QUERY, {})
        
        # 可能需要接收多个响应，找到匹配 SN 的
        for _ in range(10):
            response = await self._async_receive()
            if response and response.get('sn') == self._sn:
                msg = response.get('msg', {})
                return msg.get('data', {})
        
        return {}

    async def async_control(self, payload: dict) -> bool:
        """Send control command to device."""
        await self._async_send_command(CMD_SET, payload)
        return True